import asyncio
import os
from typing import Annotated, Any, Dict, Optional
from dotenv import load_dotenv
import asyncpg
from loguru import logger

from genai_session.session import GenAISession
from genai_session.utils.context import GenAIContext
from genai_session.utils.agents import AgentResponse
import traceback
import re
import requests

def rewrite_table_aliases(sql: str, table_aliases: Dict[str, str]) -> str:
    for alias, real_name in table_aliases.items():
        sql = re.sub(rf"\b{alias}\b", real_name, sql, flags=re.IGNORECASE)
    return sql

def rewrite_column_value_clauses(sql: str, value_mappings: Dict[str, Dict[str, str]]) -> str:
    where_pattern = re.search(r"\bWHERE\b\s+(.+)", sql, re.IGNORECASE)
    if not where_pattern:
        return sql  # No WHERE clause — skip

    condition = where_pattern.group(1)

    # Rewrite conditions for each table's mapping
    for table, mappings in value_mappings.items():
        for user_term, db_condition in mappings.items():
            # Replace exact match like: active = true
            pattern = rf"\b{user_term}\s*=\s*true\b"
            condition = re.sub(pattern, db_condition, condition, flags=re.IGNORECASE)

            # Optional: handle shorthand like just "active"
            condition = re.sub(rf"\b{user_term}\b", db_condition, condition, flags=re.IGNORECASE)

    # Reconstruct the SQL
    updated_sql = re.sub(r"\bWHERE\b\s+(.+)", f"WHERE {condition}", sql, flags=re.IGNORECASE)
    return updated_sql

# Load environment variables
load_dotenv()

TABLE_ALIASES = {
    "users": "amf_user",
    "messages": "amf_message",
    "deliveries": "amf_delivery",
}

def resolve_table_alias(sql: str) -> str:
    for alias, actual in TABLE_ALIASES.items():
        sql = sql.replace(f" {alias} ", f" {actual} ")
        sql = sql.replace(f" {alias}\n", f" {actual}\n")
        sql = sql.replace(f" {alias},", f" {actual},")
    return sql

def get_active_agent_id_by_name(agent_list: list[dict], target_name: str) -> str | None:
    """
    Finds the agent_id of an active agent matching the given name.

    Args:
        agent_list (list[dict]): List of agents from get_my_agents()
        target_name (str): The name of the agent to find

    Returns:
        str | None: agent_id if active and found, else None
    """
    for agent in agent_list:
        if (
            agent.get("agent_name") == target_name
            and agent.get("is_active", True)
        ):
            return agent.get("agent_id")
    return None

def get_my_agents(base_url) -> list[dict]:
    """
    Fetches the list of previously registered agents from the API using requests (sync).

    Returns:
        List of agent metadata dictionaries.
    """
    token = os.getenv("GENAI_JWT_TOKEN")
    if not token:
        raise ValueError("GENAI_JWT_TOKEN environment variable is not set")
    if not base_url:
        raise ValueError("API URL is not set")
    url = f"{base_url}/api/agents"
    headers = {
        "Authorization": f"Bearer {token}"
    }

    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()

AGENT_JWT = os.getenv("GENAI_JWT_TOKEN")
session = GenAISession(jwt_token=AGENT_JWT)

# Load DB connection string and schema path
PG_URL = os.getenv("GOLDEN_SAPPHIRE_DB_URL")
SCHEMA_PATH = os.getenv("GOLDEN_SAPPHIRE_DB_SCHEMA")

# Load schema content globally
DB_SCHEMA_SQL = ""
if SCHEMA_PATH:
    with open(SCHEMA_PATH, "r") as schema_file:
        DB_SCHEMA_SQL = schema_file.read()

# # Apply schema at startup (optional)
# async def apply_schema():
#     if PG_URL and DB_SCHEMA_SQL:
#         conn = await asyncpg.connect(PG_URL)
#         try:
#             await conn.execute(DB_SCHEMA_SQL)
#         except Exception as e:
#             # Can't use agent_context.logger outside session.bind scope
#             print(f"[ERROR] Failed to apply schema: {e}")
#         finally:
#             await conn.close()

# # Run schema application once at startup
# asyncio.get_event_loop().run_until_complete(apply_schema())

@session.bind(
    name="postgres_query_agent",
    description="Executes SELECT queries on PostgreSQL with provided arguments"
)
async def postgres_query_agent(
    agent_context: GenAIContext,
    request: Annotated[str, "SQL SELECT query to execute with placeholders like $1, $2, etc."],
    arguments: Annotated[Optional[Dict[str, Any]], "Dictionary of parameters to bind to the SQL query"],
) -> Any:
    """Executes SELECT queries on PostgreSQL with parameters"""
    session_url = os.getenv("GENAI_API_BASE_URL")
    if not session_url:
        raise ValueError("GENAI_API_BASE_URL environment variable is not set")
    print(f'Active agent UUID: {agent_context.agent_uuid}')
    data = get_my_agents(session_url)
    agent_context.logger.info(f"Request: {request}, Arguments: {arguments}")
#     agent_context.logger.info(f"Active agents: {data}")
#     print(f"Active agents: {data}")
#     print(f'Active agents list: {session.get_my_active_agents()}')
#     agent_name = "schema_alias_context_agent"
#     agent_context.logger.info(f'Fetching agent UUID for {agent_name}')
#     agents_list = await session.get_my_active_agents()
#     agent_context.logger.info(f'Active agents: {[agent.name for agent in agents_list]}')
#     agent_uuid = next((agent.uuid for agent in agents_list if agent.name == agent_name), None)
#     agent_context.logger.info(f'Agent UUID: {agent_uuid}')
#     if not agent_uuid:
#         raise Exception(f"Agent '{agent_name}' not found")
#     agent_context.logger.info(f"Request: {request}, Arguments: {arguments}, Agent UUID: {agent_context.agent_uuid}")
#     ctx_response: AgentResponse = await session.send({},agent_uuid)
#
#     if ctx_response.is_success:
#         alias_info = ctx_response.response
#         table_aliases = alias_info.get("table_aliases", {})
#         column_value_mappings = alias_info.get("column_value_mappings", {})
#     else:
#          raise Exception("Could not fetch schema alias context")

#     raw_sql = request.strip()  # your incoming query string
#     sql1 = rewrite_table_aliases(raw_sql, table_aliases)
#     sql2 = rewrite_column_value_clauses(sql1, column_value_mappings)
#     sql = sql2

    sql = request.strip()  # your incoming query string
    agent_context.logger.info("Executing query request")
    sql = resolve_table_alias(request.strip())
    agent_context.logger.debug(f"SQL: {sql}")
    agent_context.logger.debug(f"SQL: Original {request}")

    agent_context.logger.debug(f"Arguments: {arguments}")

    if not sql.lower().startswith("select"):
        return {
            "success": False,
            "error": "validation_error",
            "message": "Only SELECT statements are allowed."
        }

    try:
        conn = await asyncpg.connect(PG_URL)

        agent_context.logger.debug(f"Resolved SQL: {sql}")
        rows = await conn.fetch(sql, *tuple(arguments.values()) if arguments else ())
        await conn.close()
        result = [dict(row) for row in rows]
        agent_context.logger.info(f"Query returned {len(result)} rows")
#         if arguments:
#             export_format = arguments.get("export_format")  # Optional
#             if not export_format:
#                 export_format = arguments.get("format", "csv")
#
#             if export_format:
#                 agent_context.logger.info(f"Exporting result to {export_format} format")
#                 # Send export request to export_result_agent
#                 export_agent_name = "export_result_agent"  # Replace with real agent name or UUID
#                 agents_list = await session.get_my_active_agents()
#                 export_agent_uuid = next((agent.uuid for agent in agents_list if agent.name == export_agent_name), None)
#                 if not export_agent_uuid:
#                     raise Exception(f"Export agent '{export_agent_name}' not found")
#                 export_response: AgentResponse = await session.send(
#                     agent_uuid="export_result_agent",  # Replace with real UUID or alias
#                     params={
#                         "data": result,
#                         "format": export_format
#                     }
#                 )
#
#                 if export_response.is_success:
#                     export_file_path = export_response.response.get("file_path")
#                     return {
#                         "success": True,
#                         "message": "Query and export successful",
#                         "data": result,
#                         "export_file_path": export_file_path
#                     }
#                 else:
#                     return {
#                         "success": True,
#                         "message": "Query succeeded but export failed",
#                         "data": result,
#                         "export_error": export_response.response
#                     }
#         else:
        return {
            "success": True,
            "message": "Query succeeded",
            "data": result,
        }
    except Exception as e:
        tb = traceback.format_exc()
        print("Error:", e)
        print("Traceback:\n", tb)
        agent_context.logger.error(f"Database query failed: {e}")
        return {
            "success": False,
            "error": "database_error",
            "message": str(e)
        }

# @session.bind(
#     name="get_database_schema",
#     description="Returns the current SQL schema string loaded from file"
# )
# async def get_database_schema(agent_context: GenAIContext) -> str:
#     """Returns loaded database schema as text"""
#     agent_context.logger.info("Returning schema to client")
#     return DB_SCHEMA_SQL

async def main():
    print(f"Postgres Query Agent with token '{{agent_token}}' started")
    await session.process_events()

if __name__ == "__main__":
    asyncio.run(main())
