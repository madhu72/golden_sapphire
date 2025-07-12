import asyncio
import os
from typing import Dict
from dotenv import load_dotenv

from genai_session.session import GenAISession
from genai_session.utils.context import GenAIContext

load_dotenv()

AGENT_JWT = os.getenv("GENAI_JWT_TOKEN")
session = GenAISession(jwt_token=AGENT_JWT)

@session.bind(
    name="schema_alias_context_agent",
    description="Provides table aliases and common column-value mappings for semantic query translation"
)
async def schema_alias_context_agent(agent_context: GenAIContext) -> Dict:
    """Returns table aliases and semantic column-value mappings"""

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

async def main():
    print("Schema Alias Context Agent started")
    await session.process_events()

if __name__ == "__main__":
    asyncio.run(main())
