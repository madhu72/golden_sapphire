from fastmcp import FastMCP, Context
from fastapi.responses import StreamingResponse
from starlette.requests import Request
import csv
import json
import uuid
import decimal
import datetime
import aiohttp
from io import BytesIO
import io
import os
from dotenv import load_dotenv
from typing import Annotated, Any, Dict, Optional
from genai_session.session import GenAISession
from genai_session.utils.context import GenAIContext
from genai_session.utils.file_manager import FileManager
import traceback
import time
import pandas as pd
from fastapi import FastAPI
import hmac
import hashlib
import time
import base64
from urllib.parse import urlencode
from pydantic import BaseModel, Field
from typing import Literal
import sqlalchemy
from io import BytesIO
import tempfile
import asyncpg
load_dotenv()


async def get_agent_uuid_by_name(agent_name: str, jwt_token: str, api_base_url: str) -> str:
    headers = {"Authorization": f"Bearer {jwt_token}"}
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{api_base_url}/api/agents", headers=headers) as resp:
            agents = await resp.json()
            #print('Fetched agents:', json.dumps(agents, indent=4))  # Debugging: print all agents
            for agent in agents:
                #print('agents list:',json.dumps(agent, indent=4))  # Debugging: print each agent's details
                if agent.get("agent_name") == agent_name:
                    return agent["agent_id"]
    raise ValueError(f"Agent '{agent_name}' not found.")

async def fetch_query_results(pg_url: str, sql: str, arguments: dict = None) -> list[dict]:
    """
    Executes a SQL query using asyncpg and returns the result as a list of dictionaries.

    Args:
        pg_url (str): PostgreSQL connection string (e.g., postgresql://user:pass@host:port/dbname).
        sql (str): The SQL query to execute.
        arguments (dict, optional): Query parameters.

    Returns:
        list[dict]: Query result rows as dictionaries.
    """
    conn = await asyncpg.connect(pg_url)
    try:
        # Execute query with arguments if provided
        records = await conn.fetch(sql, *tuple(arguments.values()) if arguments else ())
        return [dict(r) for r in records]
    finally:
        await conn.close()

SECRET_KEY = os.getenv("SIGNED_SECRET_KEY", "very long secret key for download file securely")

def generate_signed_url(file_id: str, expires_in: int = 600):
    expires = int(time.time()) + expires_in
    data = f"{file_id}:{expires}"
    signature = hmac.new(SECRET_KEY.encode(), data.encode(), hashlib.sha256).digest()
    signature_b64 = base64.urlsafe_b64encode(signature).decode().rstrip("=")

    query = urlencode({
        "expires": expires,
        "signature": signature_b64
    })

    return f"/proxy/download/{file_id}?{query}"

from fastapi import Request, HTTPException

def verify_signature(file_id: str, expires: str, signature: str):
    if int(expires) < int(time.time()):
        raise HTTPException(status_code=403, detail="Link expired")

    data = f"{file_id}:{expires}"
    expected_sig = hmac.new(SECRET_KEY.encode(), data.encode(), hashlib.sha256).digest()
    expected_sig_b64 = base64.urlsafe_b64encode(expected_sig).decode().rstrip("=")

    if not hmac.compare_digest(signature, expected_sig_b64):
        raise HTTPException(status_code=403, detail="Invalid signature")

session = GenAISession(jwt_token=os.getenv("GENAI_JWT_TOKEN", "default_jwt_token"))

mcp = FastMCP("golden_sapphire_mcp")


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


def make_json_serializable2(row):
    return {
            k: str(v) if isinstance(v, (bytes, tuple)) else v
            for k, v in row.items()
        }



GENAI_API_BASE_URL = os.getenv("GENAI_API_BASE_URL", "http://localhost:8000")
GENAI_JWT_TOKEN = os.getenv("GENAI_JWT_TOKEN")
genai_session = GenAISession(jwt_token=GENAI_JWT_TOKEN)

class GSDataExportInput(BaseModel):
    schema_context_file_id: str = Field(..., description="File ID for uploaded schema context (e.g., JSON with aliases/descriptions)")
    schema_file_id: str = Field(..., description="File ID for uploaded raw schema definition (e.g., .sql or JSON)")
    db_config_file_id: str = Field(..., description="File ID for Database connection URL (e.g., PostgreSQL)")
    request: str = Field(..., description="Natural language data export request")
    output_format: Literal["csv", "json", "excel"] = Field("csv", description="Export format")


@mcp.custom_route("/proxy/download/{file_id}", methods=["GET"])
async def proxy_download(ctx):
    file_id = ctx.path_params.get("file_id")
    q = ctx.query_params
    signature = q.get("signature")
    expires = q.get("expires")

    if not signature or not expires:
        return {"error": "Missing signature or expiration"}

    try:
        verify_signature(file_id, expires, signature)
    except HTTPException as e:
        return {"error": e.detail}

    jwt_token = os.getenv("GENAI_JWT_TOKEN")
    api_base_url = os.getenv("GENAI_API_BASE_URL")
    headers = {"Authorization": f"Bearer {jwt_token}"}
    file_url = f"{api_base_url}/files/{file_id}"

    session = aiohttp.ClientSession()
    try:
        resp = await session.get(file_url, headers=headers)
        if resp.status != 200:
            content = await resp.text()
            await session.close()
            return {"error": f"Failed to fetch file: {resp.status}", "details": content}

        # Important: Do not exit the `session.get()` context before streaming
        stream = StreamingResponse(
            resp.content.iter_chunked(8192),
            media_type=resp.headers.get("content-type", "application/octet-stream"),
            headers={
                "Content-Disposition": resp.headers.get(
                    "content-disposition",
                    f'attachment; filename="{file_id}"'
                )
            }
        )

        # Tie stream closing to the aiohttp session
        async def close_session():
            await resp.release()
            await session.close()

        stream.background = close_session
        return stream

    except Exception as e:
        await session.close()
        return {"error": str(e)}

async def fetch_file_content(file_id: str) -> bytes:
    url = f"{GENAI_API_BASE_URL}/files/{file_id}"
    headers = {"Authorization": f"Bearer {GENAI_JWT_TOKEN}"}

    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(url) as resp:
            resp.raise_for_status()
            return await resp.read()

from fastmcp import Context

async def execute_and_export(sql: str, db_url: str, output_format: str) -> BytesIO:
    """
    Execute SQL on DB and return exported file buffer.

    Args:
        sql: Generated SQL query
        db_url: Database connection string
        output_format: One of 'csv', 'json', 'excel'

    Returns:
        BytesIO buffer containing exported data
    """
    rows = await fetch_query_results(db_url, sql)
    df = pd.DataFrame(rows)

    buffer = BytesIO()
    if output_format == "csv":
        df.to_csv(buffer, index=False)
    elif output_format == "json":
        buffer.write(json.dumps(df.to_dict(orient="records"), indent=4).encode("utf-8"))
    elif output_format == "excel":
        df = df.copy()
        df[df.select_dtypes(["datetimetz"]).columns] = df.select_dtypes(["datetimetz"]).apply(lambda x: x.dt.tz_localize(None))
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False)
    else:
        raise ValueError(f"Unsupported format: {output_format}")

    buffer.seek(0)
    return buffer

@mcp.tool(name="gs-data-export", description="Export data from database using natural language request and schema context")
async def gs_data_export( input: GSDataExportInput,ctx: Context) -> dict:
    """
    Export data from database using natural language request and schema context
    """
    jwt_token = os.getenv("GENAI_JWT_TOKEN")
    api_base_url = os.getenv("GENAI_API_BASE_URL")
    headers = ctx.request_context.request.headers
    session_id = headers.get("mcp-session-id")
    fm = FileManager(
        api_base_url=api_base_url,
        session_id=session_id,
        request_id=str(uuid.uuid4()),
        jwt_token=jwt_token
    )

    # Fetch files from AgentOS
    context_file_stream = await fm.get_by_id(input.schema_context_file_id)
    context_text = context_file_stream.read().decode("utf-8")

    schema_file_stream = await fm.get_by_id(input.schema_file_id)
    schema_text = schema_file_stream.read().decode("utf-8")

    db_config_file_stream = await fm.get_by_id(input.db_config_file_id)
    db_config_text = db_config_file_stream.read().decode("utf-8")

    # Debug/log step: print schema file snippet
    print("Schema Context Sample:", context_text[:200])
    print("Schema File Sample:", schema_text[:200])
    print("DB Config Sample:", db_config_text[:200])
    print("Request:", input.request)
    print("Output Format:", input.output_format)
    schema_context = json.loads(context_text)

    db_config = json.loads(db_config_text) if db_config_text.strip().startswith("{") else db_config_text.strip()

    # Step 3: Generate SQL from natural language
    #query = await generate_sql(input.request, schema_text, schema_context)

#     sql_result = await session.call_tool(
#                 tool="gs_sql_generator",
#                 input={
#                     "schema_context": schema_context,
#                     "schema_definition": schema_definition,
#                     "request": input.request
#                 }
#             )


    jwt_token = os.getenv("GENAI_JWT_TOKEN")
    api_base_url = os.getenv("GENAI_API_BASE_URL")
    agent_uuid = await get_agent_uuid_by_name('gs_sql_generator', jwt_token, api_base_url)
    #agent_uuid = "33024775-349d-4d05-ba9d-2fba91c9796d"
    message = {
        "schema_context": schema_context,
        "schema_definition": schema_text,
        "request": input.request
    }
    agent_response: AgentResponse = await genai_session.send(
        message=message,
        client_id=agent_uuid,
    )

    if agent_response.is_success:
        buffer = await execute_and_export(agent_response.response, db_config, input.output_format)
        #file_buffer.seek(0) # rewind to beginning before reading
        request_id = str(uuid.uuid4())
        # Upload using FileManager
        output_format = input.output_format.lower()
        if output_format not in ["csv", "json", "excel"]:
            return {"error": f"Unsupported output format: {output_format}"}
        if output_format == "excel":
            suffix = ".xlsx"
        elif output_format == "json":
            suffix = ".json"
        elif output_format == "csv":
            suffix = ".csv"
        else:
            return {"error": f"Unsupported output format: {output_format}"}
        file_id = await fm.save(buffer.read(), f"data_export_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}_{time.time_ns()}.{suffix}")
        signed_url = generate_signed_url(file_id)
        print('Signed URL for download:', signed_url)
        print("Agent Response:", agent_response.response)
        return {
            "message": "Data exported successfully",
            "download_link": f"https://svc.thotavrao.com{signed_url}"
        }
    else:
        return f"Agent call failed: {agent_response.response}"



    # Step 4: Execute query on DB
    #rows = await run_query(query, db_config)

    # Step 5: Export and upload
    #file_id, filename = await export_and_upload(rows, input.output_format, fm)

#     return {
#         "message": "Query succeeded",
#         "query": query,
#         "file_id": file_id,
#         "filename": filename,
#         "download_link": f"https://svc.thotavrao.com/proxy/download/{file_id}"
#     }
#     return {
#         "message": "Received and parsed schema files successfully",
#         "context_preview": context_text[:500],
#         "schema_preview": schema_text[:500]
#     }

@mcp.tool()
async def csv_to_json(file_id: str, ctx: Context) -> Dict:
    """
    Accepts an uploaded CSV file via file_id and returns the parsed JSON data.
    """
    try:
        if not file_id:
            return {"error": "file_id is required"}

        content = await fetch_file_content(file_id)
        #text = content.decode("utf-8")
        #reader = csv.DictReader(text.splitlines())
        #json_data = list(reader)
        df = pd.read_csv(BytesIO(content))
        json_data = df.to_dict(orient="records")


        suffix = ".json"
        filename = f"exported_data_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}{suffix}"
        jwt_token = os.getenv("GENAI_JWT_TOKEN")
        api_base_url = os.getenv("GENAI_API_BASE_URL")

        headers = ctx.request_context.request.headers
        try:
            print(make_json_serializable(ctx.request_context.request))
        except Exception as e:
            print("Error serializing request context:", e)
            print(json.dumps(ctx.request_context.request, indent=4, ensure_ascii=False))
        session_id = headers.get("mcp-session-id")

        # Make JSON serializable
        #json_data = [make_json_serializable2(row) for row in reader]

        # Write to BytesIO (in-memory file)
        file_buffer = BytesIO()
        try:
            #json.dump(json_data, file_buffer, indent=4, ensure_ascii=False)
            string_buffer = io.StringIO()
            #json.dump(json_data, string_buffer, indent=4, ensure_ascii=False)
            #file_buffer = BytesIO(string_buffer.getvalue().encode("utf-8"))
            file_bytes = json.dumps(json_data, indent=4, ensure_ascii=False).encode("utf-8")
            #file_buffer.seek(0)
        except TypeError as e:
            return {"error": f"Failed to serialize data: {str(e)}"}

        #file_buffer.seek(0) # rewind to beginning before reading
        request_id = str(uuid.uuid4())
        # Upload using FileManager
        fm = FileManager(
            api_base_url=api_base_url,
            session_id=session_id,
            request_id=request_id,
            jwt_token=jwt_token
        )
        #content_bytes = file_buffer.read()
        print(str(file_bytes)[:1000])  # Print first 1000 bytes for debugging
        file_id = await fm.save(file_bytes, filename)
        metadata = await fm.get_metadata_by_id(file_id)
        print("Uploaded file size:", json.dumps(metadata))
        print('File Id', make_json_serializable(file_id))
        # (Optional) Get uploaded file contents for verification
        content_stream = await fm.get_by_id(file_id)
        content = content_stream.read().decode("utf-8")
        time.sleep(5)
        return {
            "file_id": file_id,
            "filename": filename,
            "message": f"CSV file successfully converted to JSON with {file_id}",
            "content_preview": content[:500] ,
             #"download_link": f"https://svc.thotavrao.com/proxy/download/{file_id}"# just a preview
            "download_link": f"https://svc.thotavrao.com{generate_signed_url(file_id)}"  # Use signed URL for secure download
        }

    except Exception as e:
        tb = traceback.format_exc()
        print("Error:", e)
        print("Traceback:\n", tb)
        return {"error": str(e)}

if __name__ == "__main__":
    mcp.run(host="0.0.0.0", port=9999, transport="streamable-http")

