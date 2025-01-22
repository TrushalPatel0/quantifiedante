import json
from channels.generic.websocket import AsyncWebsocketConsumer
import websockets

class TradovateConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Accept WebSocket connection
        await self.accept()

        try:
            # Connect to Tradovate WebSocket
            self.tradovate_socket = await websockets.connect(
                'wss://demo.tradovateapi.com/v1/websocket'
            )

            # Example: Send authorization message (replace <access_token> with your token)
            access_token = "TJJTlR4Pl_vI4xl67twVEN93mvzLEnH_44xG5vyRffIpgQMqLGvM2F7sQ_tQUAmyjmg-gPHGhGOKHxEDg66OA3rKcr7eGTlJKDMd7ggRbHByrBvg2aIOMSgEALuZVgwEeegKq47gihwG5qC-i2oM_OWjBC8gOp695B9qX6XVM4O4ps1j9_MVH4WlEOz8I5cAaNWCt7-zi0VMAw"  # Replace with your access token
            auth_message = f"authorize\n1\n\n{access_token}"
            await self.tradovate_socket.send(auth_message)

            # Wait for Tradovate response
            tradovate_response = await self.tradovate_socket.recv()
            print(f"Raw Response: {tradovate_response}")

            # Check if the response is empty
            if not tradovate_response:
                await self.send(json.dumps({"error": "Received empty response from Tradovate WebSocket."}))
                await self.close()
                return

            # Parse the response using the correct method
            response_type, response_payload = self.prepare_msg(tradovate_response)

            if response_type == 'a':  # Authentication response
                if response_payload[0]["s"] == 200:
                    await self.send(json.dumps({"message": "Connected to Tradovate WebSocket!"}))
                else:
                    await self.send(json.dumps({"message": "Failed to authenticate with Tradovate WebSocket."}))
                    await self.close()
            else:
                await self.send(json.dumps({"message": "Unexpected response from Tradovate WebSocket."}))
                await self.close()

        except Exception as e:
            await self.send(json.dumps({"error": str(e)}))
            await self.close()

    async def disconnect(self, close_code):
        # Close Tradovate WebSocket if open
        if hasattr(self, 'tradovate_socket') and self.tradovate_socket:
            await self.tradovate_socket.close()

    def prepare_msg(self, raw):
        """
        Parse the raw server frame into its type and payload.
        :param raw: Raw WebSocket response from Tradovate
        :return: Tuple (frame_type, payload_data)
        """
        frame_type = raw[0]  # First character is the frame type
        try:
            payload = json.loads(raw[1:]) if len(raw) > 1 else None  # Parse the rest as JSON
        except json.JSONDecodeError:
            print(f"Failed to decode JSON from response: {raw[1:]}")
            payload = None
        return frame_type, payload


    async def receive(self, text_data):
        # Handle messages from the WebSocket client
        await self.send(json.dumps({"message": "This is a test response"}))


