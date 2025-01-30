import json
import asyncio
import websockets
import requests
import nest_asyncio
import time
from typing import Optional

import logging
logger_trades = logging.getLogger('django.success_failure_trades')


nest_asyncio.apply()
# Constants for URLs
URL = 'wss://demo.tradovateapi.com/v1/websocket'
REST_URL = 'https://demo.tradovateapi.com/v1'

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
        self.debug_label = debug_label
        self.cur_time = time.time()
        self.ws: Optional[websockets.WebSocketClientProtocol] = None
        self.heartbeat_task = None

    def increment(self):
        self.counter += 1
        return self.counter

    def get_cur_time(self):
        """Gets current time"""
        return self.cur_time

    def set_cur_time(self, t: float):
        """Sets current time if the new time is different"""
        self.cur_time = t if t != self.cur_time else self.cur_time

    async def connect(self, url, access_token):
        """Connect to the WebSocket server."""
        while True:
            try:
                print(f"Connecting to {url}...")
                self.ws = await websockets.connect(url)
                print("WebSocket connected.")
                logger_trades.info("WebSocket connected.")

                await self.authorize(access_token)
                self.heartbeat_task = asyncio.create_task(self.send_heartbeats())  # Start heartbeats
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

    async def send_heartbeats(self):
        """Send heartbeats every second and stop after 10 seconds."""
        start_time = time.time()
        while time.time() - start_time < 10:
            try:
                await self.send_raw('[]')
                print("Heartbeat sent.")
                logger_trades.info("Heartbeat sent.")
            except Exception as e:
                print(f"Failed to send heartbeat: {e}")
            await asyncio.sleep(1)  # Send heartbeat every second
        print("Stopped sending heartbeats after 10 seconds.")
        logger_trades.info("Stopped sending heartbeats after 10 seconds.")

    async def listen_to_server(self):
        """Listen for messages from the server."""
        try:
            async for msg in self.ws:
                self.set_cur_time(time.time())  # Update the current time when a message is received
                logger_trades.info("Message from Tradovate =>{}".format(msg))
        except websockets.exceptions.ConnectionClosed as e:
            print(f"WebSocket connection closed: {e}")
            logger_trades.info("Message from Tradovate =>{}".format(e))

    async def close(self):
        """Close the WebSocket connection."""
        if self.heartbeat_task:
            self.heartbeat_task.cancel()
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



async def tradovate_bracketOrder_socket(paramss, access_token, action, account_id, account_spec):
    # Check account ID
    if not account_id:
        print("No account found. Exiting.")
        return

    print("this is latest1")

    # Use the singleton socket instance
    await socket.connect(URL, access_token)

    await socket.send_order(account_id, account_spec, "MNQH5", action, paramss)
    await asyncio.sleep(7)
