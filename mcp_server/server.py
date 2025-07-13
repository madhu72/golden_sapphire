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

session = GenAISession(jwt_token=os.getenv("JWT_SECRET", "default_jwt_token"))

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

load_dotenv()

GENAI_API_BASE_URL = os.getenv("GENAI_API_BASE_URL", "http://localhost:8000")
GENAI_JWT_TOKEN = os.getenv("GENAI_JWT_TOKEN")

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

