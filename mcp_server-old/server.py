import asyncio
import os
from typing import Annotated, Any, Dict, Optional
from dotenv import load_dotenv
import asyncpg
from loguru import logger
import time
from mcp.server.fastmcp import FastMCP
from genai_session.session import GenAISession
from genai_session.utils.context import GenAIContext
from genai_session.utils.agents import AgentResponse
from genai_session.utils.file_manager import FileManager
import traceback
import re
import requests
import datetime
import decimal
import uuid

import pandas as pd
import tempfile

from fastmcp import FastMCP
from pydantic import BaseModel, ConfigDict
from loguru import logger

def make_json_serializable(obj):
    if isinstance(obj, dict):
        return {k: make_json_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [make_json_serializable(item) for item in obj]
    elif isinstance(obj, (uuid.UUID, decimal.Decimal)):
        return str(obj)
    elif isinstance(obj, (datetime.datetime, datetime.date)):
        return obj.isoformat()
    else:
        return obj


mcp = FastMCP("golden_sapphire")

# Load environment variables
load_dotenv()

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
def normalize_agent_context(ctx):
    class SafeCtx:
        def __init__(self, ctx):
            self._ctx = ctx

        def __getattr__(self, key):
            if isinstance(self._ctx, dict):
                return self._ctx.get(key)
            return getattr(self._ctx, key, None)

    return SafeCtx(ctx)





async def _schema_alias_context_agent(agent_context: Any = None) -> Dict:
    """Returns table aliases and semantic column-value mappings"""
    agent_context = normalize_agent_context(agent_context)
    agent_context = GenAIContext(
        agent_uuid=agent_context.agent_uuid,
        jwt_token=os.getenv("GENAI_JWT_TOKEN"),
        websocket=os.getenv("GENAI_WS_URL"),
        api_base_url=os.getenv("GENAI_API_BASE_URL")
    )
    #agent_context.logger = logger
    agent_context.logger.info("Returning schema alias context")

    return {
        "table_aliases": {
            "users": "amf_user",
            "messages": "amf_message",
            "deliveries": "amf_delivery",
            "customers": "amf_customer"
        },
        "column_value_mappings": {
            "amf_user": {
                "active": "active=true",
                "inactive": "active = false",
                "first_name": "given_name",
                "last_name": "surname",
                "email_address": "email",
                "phone":"phone_number",
            },
            "amf_message": {
                "message_id":"message_id::text",
                "delivered": "status = 'Delivered'",
                "failed": "status = 'Failed'",
                "held": "status = 'Held'",
                "queued": "status = 'Queued'",
                'date':'create_time',
                'message_type': 'msg_type',
                'id': 'message_id',
                'create_time': 'create_time::text',
                'file_size': 'file_size',
            },
            "amf_delivery": {
                "delivered": "status = 'Delivered'",
                "failed": "status = 'Failed'",
                "held": "status = 'Held'",
                "queued": "status = 'Queued'",
                'date':'create_time',
                'active': "deleted= false",
               'deleted': "deleted= true",
               },
               "amf_customer": {
                   # Add as needed, e.g.,
                   "customer_name": "customer",
                   "billing_id": "billing_id"
               }
        },
        "table_relationships": {
            "amf_user": {
                "customer → amf_customer.customer_id": "u.customer_id = c.customer_id",
            },
            "amf_message": {
                "sender → amf_user.user_name": "m.sender = u.user_name",
                "receiver → amf_user.user_name": "m.receiver = u.user_name",
            },
            "amf_delivery": {
                "sender → amf_user.user_name": "d.sender = u.user_name",
                "receiver → amf_user.user_name": "d.receiver = u.user_name",
                "file_size → amf_message.file_size": "d.message_id = m.message_id",
                "message_id → amf_message.message_id": "d.message_id = m.message_id",
                "status → amf_message.status": "d.message_id = m.message_id",
            }
        }
    }

@mcp.tool(exclude_args=["agent_context"])
@session.bind(
    name="schema_alias_context_agent",
    description="Provides table aliases and common column-value mappings for semantic query translation"
)
async def schema_alias_context_agent(agent_context: Any = None) -> Dict:
    return await _schema_alias_context_agent(agent_context)

@mcp.tool(exclude_args=["agent_context"])
@session.bind(
    name="postgres_query_agent",
    description="Executes SELECT queries on PostgreSQL with provided arguments"
)
async def postgres_query_agent(
    agent_context: Any = None,
    request: Annotated[str, "SQL SELECT query to execute with placeholders like $1, $2, etc."]= "",
    export_format: Annotated[str, "Optional export format (csv or excel)"] = 'excel',
    arguments: Annotated[Optional[Dict[str, Any]], "Dictionary of parameters to bind to the SQL query"] = None,
) -> Any:
    agent_context = normalize_agent_context(agent_context)
    agent_context = GenAIContext(
            agent_uuid=agent_context.agent_uuid,
            jwt_token=os.getenv("GENAI_JWT_TOKEN"),
            websocket=None,
            api_base_url=os.getenv("GENAI_API_BASE_URL")
        )
    """Executes SELECT queries on PostgreSQL with parameters"""
    session_url = os.getenv("GENAI_API_BASE_URL")
    if not session_url:
        raise ValueError("GENAI_API_BASE_URL environment variable is not set")
    print(f'Active agent UUID: {agent_context.agent_uuid}')
    data = get_my_agents(session_url)
    agent_context.logger.info(f"Request: {request}, Arguments: {arguments}")

    #alias_context = await _schema_alias_context_agent(agent_context)
    #alias_context = await agent_context.call_tool("schema_alias_context_agent")

    #agent_context.logger.info(f"Schema Context: {alias_context}")

    sql = request.strip()  # your incoming query string
    agent_context.logger.info("Executing query request")
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
        for row in result:
            for key, value in row.items():
                row[key] = make_json_serializable(value)
        agent_context.logger.info(f"Query returned {len(result)} rows")
        if export_format:
           df = pd.DataFrame(result)
           suffix = ".csv" if export_format == "csv" else ".xlsx"
           filename = f"exported_data_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}{suffix}"
           tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
           file_path = tmp_file.name

           try:

               if export_format == "csv":
                   df.to_csv(file_path, index=False)
               elif export_format == "excel":
                   df.to_excel(file_path, index=False)
               else:
                   raise ValueError("Unsupported export format")
               print(f"Exported result to {file_path} in format {export_format}")
               print(f"{agent_context.session_id} {agent_context.request_id}")
               fm = FileManager(api_base_url=os.getenv("GENAI_API_BASE_URL"), session_id=agent_context.session_id,request_id=agent_context.request_id,jwt_token=AGENT_JWT)
               with open(file_path, "rb") as f:
                    file_bytes = f.read()
               basename = os.path.basename(file_path)
               file_id = await fm.save(file_bytes, basename)

               agent_context.logger.info(f"Exported result to {file_path} with file_id {file_id}")
               agent_context.logger.info(f"Exported result to {file_path}")
               file_service_url = os.getenv("GENAI_API_BASE_URL", "http://localhost:8000")
               print('File Id', make_json_serializable(file_id))
               download_url = f"{file_service_url}/files/{file_id}"
               content = await fm.get_by_id(file_id),
               time.sleep(5)
               return {
                   "success": True,
                   "message": f"Query and export to {export_format} successful",
               }
           except Exception as ex:
               agent_context.logger.error(f"Export failed: {ex}")
               return {
                   "success": True,
                   "message": "Query succeeded but export failed",
                   #"data": result,
                   "export_error": str(ex)
               }
        else:
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


async def main():
    print(f"MCP Server with token '{{agent_token}}' started")
    #await session.process_events()
    mcp.run(host="0.0.0.0", port=9999,transport="streamable-http")

if __name__ == "__main__":
    print(f"MCP Server with token '{{agent_token}}' started")
    mcp.run(host="0.0.0.0", port=9999,transport="streamable-http")