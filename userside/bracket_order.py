import json
import asyncio
import websockets
import requests
import asyncio
import nest_asyncio
import aiohttp

# from client import Client

# Apply nest_asyncio to allow multiple event loop calls
nest_asyncio.apply()


credentials = {
    "name":       "Your credentials here",
    "password":   "Your credentials here",
    "appId":      "Sample App",
    "appVersion": "1.0",
    "cid":        0,
    "sec":        'Your API secret here'
}


# Constants for URLs
URL = 'wss://demo.tradovateapi.com/v1/websocket'
REST_URL = 'https://demo.tradovateapi.com/v1'

# Credentials


# Order Parameters
# params = {
#     "entryVersion": {
#         "orderQty": 1,
#         "orderType": "Market"
#     },
#     "brackets": [{
#         "qty": 1,
#         "profitTarget": -30,
#         "stopLoss": 15,
#         "trailingStop": False
#     }]
# }




class TradovateSocket:
    def __init__(self, debug_label="tvSocket"):
        self.counter = 0
        self.ws = None
        self.debug_label = debug_label

    def increment(self):
        self.counter += 1
        return self.counter

    async def connect(self, url, access_token):
        """Connect to the WebSocket server."""
        while True:
            try:
                print(f"Connecting to {url}...")
                self.ws = await websockets.connect(url)
                print("WebSocket connected.")
                await self.authorize(access_token)
                asyncio.create_task(self.listen_to_server())  # Start listening
                break
            except websockets.exceptions.ConnectionClosed as e:
                print(f"Connection closed: {e}. Reconnecting...")
                await asyncio.sleep(2)
            except Exception as e:
                print(f"Connection error: {e}. Retrying...")
                await asyncio.sleep(2)

    async def authorize(self, access_token):
        """Authorize the WebSocket using the access token."""
        message = f"authorize\n0\n\n{access_token}"
        await self.send_raw(message)
        print("Authorization sent.")

    async def send_order(self, account_id, account_spec, symbol, action,paramss):
        """Send an order to the WebSocket."""
        body = {
            "accountId": account_id,
            "accountSpec": account_spec,
            "symbol": symbol,
            "action": action,
            "orderStrategyTypeId": 2,
            "params": json.dumps(paramss)
        }
        message_id = self.increment()
        message = f"orderstrategy/startorderstrategy\n{message_id}\n\n{json.dumps(body)}"
        print(f"Sending order: {message}")
        await self.send_raw(message)

    async def send_raw(self, message):
        """Send a raw message to the WebSocket."""
        try:
            await self.ws.send(message)
        except Exception as e:
            print(f"Failed to send message: {e}")

    async def listen_to_server(self):
        """Listen for messages from the server."""
        try:
            while True:
                message = await self.ws.recv()
                # print(f"Received: {message}")
        except websockets.exceptions.ConnectionClosed as e:
            print(f"WebSocket connection closed: {e}")

    async def close(self):
        """Close the WebSocket connection."""
        if self.ws:
            await self.ws.close()
            print("WebSocket closed.")


# async def get_access_token(credentials):
#     async with aiohttp.ClientSession() as session:
#         async with session.post(f"{REST_URL}/auth/accessTokenRequest", json=credentials) as response:
#             response.raise_for_status()
#             return await response.json()


def get_account_id(access_token):
    """Fetch the first account ID using the REST API."""
    response = requests.get(
        f"{REST_URL}/account/list",
        headers={"Authorization": f"Bearer {access_token}", "Accept": "application/json"}
    )
    response.raise_for_status()
    accounts = response.json()
    if accounts:
        return accounts[0]["id"], accounts[0]["name"]
    return None, None


async def tradovate_bracketOrder_socket(paramss,access_tokenn,action):

    account_id, account_spec = get_account_id(access_tokenn)
    if not account_id:
        print("No account found. Exiting.")
        return
    
    socket = TradovateSocket()
    await socket.connect(URL, access_tokenn)

    await socket.send_order(account_id, account_spec, "MNQH5", action,paramss)

    await asyncio.sleep(1)
        

