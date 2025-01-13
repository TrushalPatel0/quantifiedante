import asyncio
import json
import logging
import time
import websockets
from typing import Callable, Dict, List, Any, Optional

# --- Data ---
URL = 'https://demo.tradovateapi.com/v1'
MD_URL = 'wss://md.tradovateapi.com/v1/websocket'
WS_DEMO_URL = 'wss://demo.tradovateapi.com/v1/websocket'
WS_LIVE_URL = 'wss://live.tradovateapi.com/v1/websocket'

credentials = {
    "name":       "Your credentials here",
    "password":   "Your credentials here",
    "appId":      "Sample App",
    "appVersion": "1.0",
    "cid":        0,
    "sec":        'Your API secret here'
}


# --- Utilities ---
async def wait_for_ms(ms: int):
    """Asynchronously waits for a specified number of milliseconds."""
    await asyncio.sleep(ms / 1000)


# --- Storage ---
class SessionStorage:
    """Emulates sessionStorage functionality using a simple dictionary."""
    _storage = {}

    @staticmethod
    def get_item(key: str) -> Optional[Dict]:
        """Retrieves an item from storage or None."""
        return SessionStorage._storage.get(key)

    @staticmethod
    def set_item(key: str, value: Any):
         """Sets or updates the value in storage"""
         SessionStorage._storage[key] = value


def get_user_data():
    """Retrieves user data from session storage"""
    return SessionStorage.get_item('tradovate-user-data') or {}


def set_user_data(value: Dict):
    """Sets user data in session storage"""
    SessionStorage.set_item('tradovate-user-data', value)


# --- Services ---
async def tv_get(endpoint: str, query: Optional[Dict] = None) -> Optional[Dict]:
    """Makes an authorized GET request to the Tradovate API."""
    access_token = get_user_data().get('accessToken')

    try:
        q = ""
        if query:
            q = "?" + "&".join(f"{key}={value}" for key, value in query.items())

        url = URL + endpoint + q
        logging.debug(f"GET: {url}")
        
        async with websockets.connect(url.replace('wss://','https://')) as ws:
          response = await ws.send(json.dumps(
              {
                    "method": "GET",
                    "headers": {
                        "Authorization": f"Bearer {access_token}",
                        "Accept": "application/json",
                        "Content-Type": "application/json"
                    }
              }
          ))
          raw = await ws.recv()
          js = json.loads(raw)
          
          return js

    except Exception as err:
        logging.error(f"Error during GET request: {err}")
        return None

async def tv_post(endpoint: str, data: Dict, use_token: bool = True) -> Optional[Dict]:
    """Makes an authorized POST request to the Tradovate API."""
    access_token = get_user_data().get('accessToken')
    bearer = {"Authorization": f"Bearer {access_token}"} if use_token else {}
    try:
      async with websockets.connect(URL + endpoint.replace('wss://','https://')) as ws:
        response = await ws.send(json.dumps(
            {
                "method": "POST",
                "headers": {
                    **bearer,
                    "Accept": "application/json",
                    "Content-Type": "application/json"
                },
                "body": data
            }
        ))
        raw = await ws.recv()
        js = json.loads(raw)
        return js
    
    except Exception as err:
        logging.error(f"Error during POST request: {err}")
        return None

# --- WebSocket ---
class TradovateSocket:
    """A generic implementation for the Tradovate real-time APIs WebSocket client."""

    def __init__(self, debug_label: str = 'tvSocket'):
        self.counter = 0
        self.cur_time = time.time()  # Use time.time() for timestamp
        self.listening_url = ''
        self.debug_label = debug_label
        self.ws: Optional[websockets.WebSocketClientProtocol] = None
        self.connected = False
        self.listeners: List[Callable[[Dict], None]] = []
        self.event_listener: Optional[websockets.WebSocketClientProtocol] = None


    def increment(self):
        """Increments and returns a counter"""
        self.counter += 1
        return self.counter

    def get_cur_time(self):
        """Gets current time"""
        return self.cur_time

    def set_cur_time(self, t: float):
        """Sets current time if the new time is different"""
        self.cur_time = t if t != self.cur_time else self.cur_time

    def add_listener(self, listener: Callable[[Dict], None]) -> Callable[[], None]:
        """Adds a listener and returns a function to remove it."""
        self.listeners.append(listener)
        def remove_listener():
            self.listeners.remove(listener)
        return remove_listener

    async def connect(self, url: str, token: str):
        """Connects to a Tradovate WebSocket URL and authorizes."""
        logging.info(f"{self.debug_label}: Connecting to {url}...")
        self.listening_url = url
        try:
            self.ws = await websockets.connect(url)
        except Exception as e:
          logging.error(f'connection to {url} refused with: {e}')
        
        async def message_handler():
            try:
               async for msg in self.ws:
                 if msg:
                   self.set_cur_time(check_heartbeats(self.ws, self.get_cur_time()))
                   T, data = prepare_message(msg)

                   logging.debug(f"{self.debug_label}\n {T} {data}")
                   if T == 'a' and data and len(data) > 0:
                       for listener in self.listeners:
                           for d in data:
                              listener(d)
            except Exception as e:
                logging.error(f"Connection closed unexpectedly: {e}")


        async def auth_handler():
            try:
                async for msg in self.ws:
                  if msg:
                    T, _ = prepare_message(msg)
                    if T == 'o':
                      await self.send({
                        'url': 'authorize',
                        'body': token,
                        'on_response': lambda _ : None,
                        'on_reject': lambda _ :  None,
                        'auth': True
                        })

                      return
            except Exception as e:
                logging.error(f"Authorization failed: {e}")

        self.event_listener = asyncio.create_task(message_handler())

        await auth_handler()
        logging.info(f"{self.debug_label}: Connection established.")

    async def send(self, params: Dict):
        """Sends a message via the authorized WebSocket, returns a promise."""
        url = params.get('url')
        query = params.get('query')
        body = params.get('body')
        on_response = params.get('on_response')
        on_reject = params.get('on_reject')
        auth = params.get('auth') or False

        id = self.increment()
        logging.debug(f'sending: {url}  query: {query}  body: {body}')
        msg = f"{url}\n{id}\n{query or ''}\n{json.dumps(body)}"
        
        if auth:
            await self.ws.send(msg)
            return 

        async def event_handler():
          try:
            async for raw in self.ws:
              if raw:
                _, data = prepare_message(raw)

                for item in data:
                   if item.get('s') == 200 and item.get('i') == id:
                      if on_response:
                        on_response(item)
                      return item
                   elif item.get('s') and item.get('s') != 200 and item.get('i') and item.get('i') == id:
                      logging.error(f"FAILED:\n\toperation '{url}'\n\tquery {json.dumps(query, indent=2) if query else ''}\n\tbody {json.dumps(body, indent=2) if body else ''}\n\treason '{json.dumps(item.get('d'), indent=2) or 'unknown'}'")
                      if on_reject:
                         on_reject()
                      return {"error":f"failed with {item.get('d')}"}
          except Exception as e:
               logging.error(f'error in event handler {e}')

        
        task = asyncio.create_task(event_handler())
        await self.ws.send(msg)
        return await task

    async def subscribe(self, params: Dict) -> Callable[[], None]:
        """Creates a subscription to a real-time data endpoint."""
        url = params.get('url')
        body = params.get('body')
        subscription = params.get('subscription')
        
        remove_listener = lambda : None
        cancel_url = ''
        cancel_body = {}
        contract_id = None

        response = await self.send({'url': url, 'body': body})

        if response is None:
            logging.error(f"Failed to get a valid response during subscription to {url} with body {body}")
            return lambda: None  # Return a no-op cancel function
        
        if response and response.get('d') and response.get('d').get('p-ticket'):
          await wait_for_ms(response.get('d').get('p-time')*1000)
          response = await self.send({'url': url, 'body': {**body, 'p-ticket': response.get('d').get('p-ticket')}})
        
        if response is None:
            logging.error(f"Failed to get a valid response during second request to {url} with body {body}")
            return lambda: None  # Return a no-op cancel function

        realtime_id = response.get('d',{}).get('realtimeId') or response.get('d',{}).get('subscriptionId')

        if body.get('symbol') and not body.get('symbol').startswith('@'):
            contract_res = await tv_get('/contract/find', {'name': body.get('symbol')})
            contract_id = contract_res.get('id') if contract_res else None
            if not contract_id:
                suggests = await tv_get('/contract/suggest', {'name': body.get('symbol')})
                contract_id = suggests[0].get('id') if suggests else None
            
        if not realtime_id and response.get('d',{}).get('users'):
             subscription(response.get('d'))

        
        def internal_listener(data: Dict):
           if url.lower() == 'md/getchart':
              if data.get('d',{}).get('charts'):
                 for chart in data.get('d',{}).get('charts'):
                    if chart.get('id') == realtime_id:
                      subscription(chart)
           elif url.lower() == 'md/subscribedom':
                if data.get('d',{}).get('doms'):
                   for dom in data.get('d',{}).get('doms'):
                      if dom.get('contractId') == contract_id:
                        subscription(dom)
           elif url.lower() == 'md/subscribequote':
              if data.get('d',{}).get('quotes'):
                 for quote in data.get('d',{}).get('quotes'):
                    if quote.get('contractId') == contract_id:
                       subscription(quote)
           elif url.lower() == 'md/subscribehistogram':
             if data.get('d',{}).get('histograms'):
                 for histogram in data.get('d',{}).get('histograms'):
                    if histogram.get('contractId') == contract_id:
                       subscription(histogram)
           elif url.lower() == 'user/syncrequest':
              if data.get('d',{}).get('users') or data.get('e') == 'props':
                  subscription(data.get('d'))

        if url.lower() == 'md/getchart':
             cancel_url = 'md/cancelChart'
             cancel_body = {'subscriptionId': realtime_id}
             if self.listening_url != MD_URL:
                raise ValueError('Cannot subscribe to Chart Data without using the Market Data URL.')
             remove_listener = self.add_listener(internal_listener)
        elif url.lower() == 'md/subscribedom':
            cancel_url = 'md/unsubscribedom'
            cancel_body = {'symbol': body.get('symbol')}
            if self.listening_url != MD_URL:
              raise ValueError('Cannot subscribe to DOM Data without using the Market Data URL.')
            remove_listener = self.add_listener(internal_listener)
        elif url.lower() == 'md/subscribequote':
            cancel_url = 'md/unsubscribequote'
            cancel_body = {'symbol': body.get('symbol')}
            if self.listening_url != MD_URL:
              raise ValueError('Cannot subscribe to Quote Data without using the Market Data URL.')
            remove_listener = self.add_listener(internal_listener)
        elif url.lower() == 'md/subscribehistogram':
            cancel_url = 'md/unsubscribehistogram'
            cancel_body = {'symbol': body.get('symbol')}
            if self.listening_url != MD_URL:
              raise ValueError('Cannot subscribe to Histogram Data without using the Market Data URL.')
            remove_listener = self.add_listener(internal_listener)
        elif url.lower() == 'user/syncrequest':
           if self.listening_url != WS_DEMO_URL and url != WS_LIVE_URL:
               raise ValueError('Cannot subscribe to User Data without using one of the Demo or Live URLs.')
           remove_listener = self.add_listener(internal_listener)
        else:
            raise ValueError('Incorrect URL parameters provided to subscribe.')
        
        async def cancel_subscription():
          remove_listener()
          if cancel_url:
              await self.send({'url': cancel_url, 'body': cancel_body})

        return cancel_subscription


def check_heartbeats(socket: websockets.WebSocketClientProtocol, cur_time: float) -> float:
    """Sends a heartbeat if necessary."""
    now = time.time()
    if now - cur_time >= 2.5:
        asyncio.create_task(socket.send('[]'))
        return now
    return cur_time


def prepare_message(raw: str) -> tuple[str, Any]:
    """Parses a raw websocket message."""
    T = raw[0]
    data = json.loads(raw[1:]) if len(raw) > 1 else []
    return T, data


# --- Auth ---
async def get_access_token(url: str, credentials: Dict) -> Dict:
    """Fetches an access token from the Tradovate API."""
    auth_response = await tv_post('/auth/accesstokenrequest', credentials, False)
    logging.info(auth_response)
    return auth_response

# --- Main ---
async def main():
    """Main function to run the example."""
    logging.basicConfig(level=logging.DEBUG)

    # 1. Get Access Token and Initialize Socket
    # user_data = await get_access_token(URL, credentials)
    # set_user_data(user_data)

    # access_token = user_data.get('accessToken')
    access_token = "8Y3WxHZAM2vdpTOPQpidwDswwcTHzeG7Yh4ur6oiSJ85NevlEv3ueg0HT1lT5U09jUkfhyPFsMQ8eHlOpN3oxus5ibM1_VFalJ8OrBLpDkT5dzGY9ri0wlGsjzJ4P8BG5TuRqArV37cilMgYKoQgq8kVmrJOKzxDD8rhgAKlocgxXClPdYxvS77XOBT9sr1SESB9uboBCele9a4"

    quote_socket = TradovateSocket(debug_label='quote data')
    await quote_socket.connect(MD_URL, access_token)

    # 2. Subscription parameters
    contract_name = 'MNQH5'  # <--- Specify the contract you want to watch here

    async def quote_handler(quote_data: Dict):
        """Processes and displays incoming quote data."""
        logging.info(f"MNQH5 Quote Update: {json.dumps(quote_data, indent=2)}")
        # You can add any desired quote information processing here
        # For example, to view bid/ask:
        bid = quote_data.get('bid')
        ask = quote_data.get('ask')
        if bid and ask:
            logging.info(f"   Bid: {bid}, Ask: {ask}")

    # 3. Subscribe to Quote Data
    unsubscribe = await quote_socket.subscribe({
        'url': 'md/subscribequote',
        'body': {'symbol': contract_name},
        'subscription': quote_handler
    })


    # Keep the program running to listen for events.
    try:
      while True:
        await asyncio.sleep(1)  # Keep the program alive to receive updates.
    except asyncio.CancelledError:
        pass
    finally:
        await unsubscribe()
        logging.info('done')
        if quote_socket.ws:
           await quote_socket.ws.close()

if __name__ == '__main__':
    asyncio.run(main())