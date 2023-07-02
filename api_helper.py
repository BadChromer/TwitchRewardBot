import aiohttp

async def refresh_access_token(refresh_token: str):
    params = {
    "client_id": "", # App's client id
    "client_secret": "", # App's client_secret
    "grant_type": "refresh_token",
    "refresh_token": refresh_token
    }
    async with aiohttp.ClientSession() as session:
        async with session.post("https://id.twitch.tv/oauth2/token", params=params) as response:
            token = await response.json()
            return token.get("access_token")