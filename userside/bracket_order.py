import json
import asyncio
import websockets
import requests
import asyncio
import nest_asyncio
import aiohttp
import time 

import logging
logger_trades = logging.getLogger('django.success_failure_trades')

async def tradovate_bracketOrder_socket(paramss, access_token, action, account_id, account_spec):
    nest_asyncio.apply()
    # Constants for URLs
    URL = 'wss://demo.tradovateapi.com/v1/websocket'
    REST_URL = 'https://demo.tradovateapi.com/v1'

    # Credentials


    # Order Parameters
    params = {
        "entryVersion": {
            "orderQty": 1,
            "orderType": "Market"
        },
        "brackets": [{
            "qty": 1,
            "profitTarget": -20,
            "stopLoss": 15,
            "trailingStop": False
        }]
    }



    class SingletonMeta(type):
        """A metaclass for implementing the Singleton pattern."""
        _instances = {}

        def __call__(cls, *args, **kwargs):
            if cls not in cls._instances:
                # Create a new instance if it doesn't already exist
                instance = super().__call__(*args, **kwargs)
                cls._instances[cls] = instance
            return cls._instances[cls]


    class TradovateSocket(metaclass=SingletonMeta):
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
                    logger_trades.info("WebSocket connected.")

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
            logger_trades.info("Authorization sent.")

        async def send_order(self, account_id, account_spec, symbol, action, paramss):
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
            logger_trades.info("Sending this data to Tradovate =>{}".format(message))
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
                    print(f"Received: {message}")
                    logger_trades.info("Message from Tradovate =>",message)

            except websockets.exceptions.ConnectionClosed as e:
                print(f"WebSocket connection closed: {e}")

        async def close(self):
            """Close the WebSocket connection."""
            if self.ws:
                await self.ws.close()
                print("WebSocket closed.")
                logger_trades.info("WebSocket closed.")
        
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


    # Singleton instance of TradovateSocket
    socket = TradovateSocket()

    # Function to execute the bracket order

    # account_id, account_spec = get_account_id(access_token)
    if not account_id:
        print("No account found. Exiting.")
        return


    print("this is latest1")

    # Use the singleton socket instance
    await socket.connect(URL, access_token)

    await socket.send_order(account_id, account_spec, "MNQH5", action, paramss)
    await asyncio.sleep(2)
    # await socket.close()
    # del socket
    # import gc
    # gc.collect()  





# async def main():
#     # Get access token
#     # token_data = await get_access_token(credentials)
#     # print(f"this is Token Data: {token_data}")
#     # access_token = token_data["accessToken"]
#     access_token = "rMICG5Mor_N-h10hcTQM_up3Le-A3Tbrhj_oQYk6x9ue3nVWOU2ZdqNheoEk6BZkT8efUIAH3PUCfPJY6A_vaDKmptLz2OBoqsTecmLAm0RumW1Co9K8Gbh_M9i_ugOi3CM5RlptUIzrA_Y93LjE2fRhDwA6H3j0hklXNrwmtqaEwd82kAqXH3fzF3FUAdts5n8YaGt4RVvt"   
#     print(f"Access Token: {access_token}")

#     # Get account details
#     account_id, account_spec = get_account_id(access_token)
#     if not account_id:
#         print("No account found. Exiting.")
#         return

  
#     await socket.connect(URL, access_token)

#     # Send an order
#     await socket.send_order(account_id, account_spec, "MNQH5", "Sell",params)
    
#     # await asyncio.sleep(1)
#     # Keep the connection alive
    
#     await asyncio.sleep(1)
#     # client = Client()
#     # client.get_account()

# asyncio.run(main())