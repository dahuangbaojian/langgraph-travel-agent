"""Travel Agent Authentication Module"""

from langgraph_sdk import Auth

auth = Auth()


@auth.authenticate
async def authenticate(authorization: str) -> str:
    """Enable all users for travel agent."""
    return "travel_user"
