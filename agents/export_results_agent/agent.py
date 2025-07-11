import asyncio
import os
import tempfile
import pandas as pd
from typing import Annotated, List, Dict, Union
from dotenv import load_dotenv

from genai_session.session import GenAISession
from genai_session.utils.context import GenAIContext

load_dotenv()

AGENT_JWT = os.getenv("GENAI_JWT_TOKEN")
session = GenAISession(jwt_token=AGENT_JWT)

@session.bind(
    name="export_result_agent",
    description="Exports query result into CSV or Excel format"
)
async def export_result_agent(
    agent_context: GenAIContext,
    data: Annotated[List[Dict[str, Union[str, int, float]]], "List of dictionaries to export"],
    format: Annotated[str, "Export format: 'csv' or 'excel'"]
) -> Dict[str, str]:
    """Exports result data to CSV or Excel and returns the file path"""

    agent_context.logger.info(f"Exporting {len(data)} records to format: {format}")

    try:
        if not data:
            return {"error": "No data to export"}

        df = pd.DataFrame(data)

        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{format.lower()}") as tmpfile:
            if format.lower() == "csv":
                df.to_csv(tmpfile.name, index=False)
            elif format.lower() in ("xlsx", "excel"):
                df.to_excel(tmpfile.name, index=False)
            else:
                return {"error": f"Unsupported format: {format}"}

            agent_context.logger.info(f"Exported file saved at: {tmpfile.name}")
            return {
                "success": True,
                "message": "Export successful",
                "file_path": tmpfile.name
            }

    except Exception as e:
        agent_context.logger.exception("Export failed")
        return {
            "success": False,
            "error": "export_error",
            "message": str(e)
        }

async def main():
    print(f"Export Agent started with token '{AGENT_JWT}'")
    await session.process_events()

if __name__ == "__main__":
    asyncio.run(main())
