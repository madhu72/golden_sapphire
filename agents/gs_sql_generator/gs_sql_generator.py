import asyncio
from typing import Annotated
from genai_session.session import GenAISession
from genai_session.utils.context import GenAIContext
from dotenv import load_dotenv
load_dotenv()
import openai
import os

openai.api_key = os.getenv("OPENAI_API_KEY")
import os
AGENT_JWT = os.getenv("GENAI_JWT_TOKEN") # noqa: E501
session = GenAISession(jwt_token=AGENT_JWT)

@session.bind(
    name="gs_sql_generator",
    description="Generate SQL query based on schema context, raw schema definition, and a natural language request."
)
async def generate_sql(agent_context: GenAIContext, schema_context: str, schema_definition: str, request: str) -> str:
    """
    Generates an SQL query from natural language based on schema info.

    Args:
        schema_context (str): JSON or structured data describing table/column aliases and descriptions.
        schema_definition (str): Raw schema (e.g., SQL DDL or JSON defining the structure).
        request (str): A natural language request to generate SQL for.

    Returns:
        str: A valid SQL query as per the schema and request.
    """
    prompt = f"""
You are an expert data engineer. Given the following schema context and raw schema definition,
generate a valid SQL query to satisfy the request.

Schema Context:
{schema_context}

Raw Schema Definition:
{schema_definition}

Request:
{request}

SQL Query:
"""
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You're a helpful assistant"},
            {"role": "user", "content": prompt}
        ]
    )

    sql = response.choices[0].message["content"]
    return sql


async def main():
    print(f"Agent with token '{AGENT_JWT}' started")
    await session.process_events()

if __name__ == "__main__":
    asyncio.run(main())
