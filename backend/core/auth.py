import base64
import os
import time
import httpx

TOKEN_URL = "https://api-uat.cotality.com/oauth/token?grant_type=client_credentials"

_cache = {"token": None, "expires_at": 0.0}

async def get_oauth_token() -> str:
    now = time.time()
    if _cache["token"] and now < _cache["expires_at"]:
        return _cache["token"]

    client_id = os.getenv("CLIENT_ID", "")
    client_secret = os.getenv("CLIENT_SECRET", "")
    if not client_id or not client_secret:
        raise RuntimeError("Missing CLIENT_ID or CLIENT_SECRET in .env")

    auth_string = f"{client_id}:{client_secret}"
    encoded_auth = base64.b64encode(auth_string.encode("utf-8")).decode("utf-8")

    headers = {
        "Authorization": f"Basic {encoded_auth}",
        "Content-Type": "application/x-www-form-urlencoded",
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            TOKEN_URL,
            data={"grant_type": "client_credentials"},
            headers=headers,
        )
        response.raise_for_status()
        token = response.json()["access_token"]

    # keep 55 mins
    _cache["token"] = token
    _cache["expires_at"] = now + 55 * 60
    return token