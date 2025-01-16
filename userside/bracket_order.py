import json
import requests
import websockets
import logging
import threading
import time
from userside.tradovate_functionalities import get_accounts

URL = 'wss://demo.tradovateapi.com/v1/websocket'
REST_URL = 'https://demo.tradovateapi.com/v1'

class TradovateSocket:
    def _init_(self, debug_label="tvSocket"):
        self.counter = 0
        self.ws = None
        self.debug_label = debug_label
        self.is_connected = False
        self.connection_thread = None


    def increment(self):
        self.counter += 1
        return self.counter

    def connect(self, url, access_token):
        """Connect to the WebSocket server."""
        self.access_token = access_token
        self.url = url
        self.connection_thread = threading.Thread(target=self._connect_thread)
        self.connection_thread.daemon = True  # Allow the thread to be killed when the main program ends
        self.connection_thread.start()
    
    def _connect_thread(self):
        while True:
            try:
                self.ws = websockets.connect(self.url)
                self.ws = self.ws._enter_()
                self.authorize(self.access_token)
                self.is_connected = True
                self.listen_to_server()
                break
            except websockets.exceptions.ConnectionClosed as e:
                time.sleep(2)
            except Exception as e:
                time.sleep(2)
    
    def authorize(self, access_token):
         """Authorize the WebSocket using the access token."""
         message = f"authorize\n0\n\n{access_token}"
         self.send_raw(message)

    def send_order(self, account_id, account_spec, symbol, action, params):
         """Send an order to the WebSocket."""
         body = {
             "accountId": account_id,
             "accountSpec": account_spec,
             "symbol": symbol,
             "action": action,
             "orderStrategyTypeId": 2,
             "params": json.dumps(params)
         }
         message_id = self.increment()
         message = f"orderstrategy/startorderstrategy\n{message_id}\n\n{json.dumps(body)}"
         self.send_raw(message)

    def send_raw(self, message):
         """Send a raw message to the WebSocket."""
         try:
             self.ws.send(message)
         except Exception as e:
             print(f"Failed to send message: {e}")
    
    def listen_to_server(self):
        """Listen for messages from the server."""
        try:
            while True:
                message = self.ws.recv()
        except websockets.exceptions.ConnectionClosed as e:
            self.is_connected = False
        except Exception as e:
            self.is_connected = False

    def close(self):
        """Close the WebSocket connection."""
        if self.ws:
            self.ws.close()
            self.is_connected = False
        if self.connection_thread:
            self.connection_thread.join()



def get_tradovate_socket(access_token):
    
     # Get account details
    account_info = get_accounts(access_token)
    account_spec = account_info[0]['name']
    account_id = account_info[0]['id']
    if not account_id:
         return None

    # Connect to WebSocket
    socket = TradovateSocket()
    socket.connect(URL, access_token)

    # Return the socket and account details
    return socket, account_id, account_spec