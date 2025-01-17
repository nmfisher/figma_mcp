from typing import Any
import asyncio
import json
import websockets
import aioconsole  # For async console input
import logging

WEBSOCKET_PORT = 8765

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FigmaBridge:
    """Manages WebSocket connection to Figma plugin."""
    
    def __init__(self, port: int):
        self.port = port
        self.websocket = None
        self.pending_commands = {}
        
    async def connect(self) -> None:
        """Start WebSocket server and wait for client connection."""
        self.server = await websockets.serve(self._handle_connection, "localhost", self.port)
        
    async def _handle_connection(self, websocket: websockets.WebSocketServerProtocol) -> None:
        """Handle new WebSocket connections."""
        self.websocket = websocket
        try:
            async for message in websocket:
                await self._handle_message(message)
        except websockets.exceptions.ConnectionClosed:
            logger.info("Client disconnected!")
            self.websocket = None
            
    async def _handle_message(self, message: str) -> None:
        """Process incoming WebSocket messages."""
        try:
            logger.info(f"Got message {message}")
            data = json.loads(message)
            if "id" in data and data["id"] in self.pending_commands:
                future = self.pending_commands.pop(data["id"])
                if "error" in data:
                    future.set_exception(Exception(data["error"]["message"]))
                else:
                    future.set_result(data["result"])
            logger.info(f"Received response: {data}")  # Print all responses for visibility
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            
    async def send_command(self, method: str, params: Any) -> Any:
        """Send command to Figma plugin and await response."""
        if not self.websocket:
            raise ValueError("No Figma plugin connected")
            
        command_id = f"{method}-{len(self.pending_commands)}"
        future = asyncio.Future()
        self.pending_commands[command_id] = future
        
        try:
            await self.websocket.send(json.dumps({
                "jsonrpc": "2.0",
                "id": command_id,
                "method": method,
                **params
            }))
            return await asyncio.wait_for(future, timeout=5.0)
        except asyncio.TimeoutError:
            self.pending_commands.pop(command_id, None)
            raise TimeoutError(f"Command {method} timed out")

    def is_connected(self) -> bool:
        """Check if a client is currently connected."""
        return self.websocket is not None

async def handle_user_input(bridge: FigmaBridge):
    """Handle user input and send commands to the client."""
    logger.info("\nEnter commands in format: method params")
    logger.info("Example: create-rectangle {\"x\": 100, \"y\": 100, \"width\": 200, \"height\": 100}")
    logger.info("Type 'exit' to quit\n")
    
    while True:
        try:
            command = await aioconsole.ainput("> ")
            logger.info(f"Command {command}")
            if command.lower() == 'exit':
                break
                
            try:
                result = await bridge.send_command(command, "")                 
                
                
                # Send command to client
                try:
                    logger.info(f"Command result: {result}")
                except TimeoutError as e:
                    logger.error(f"Command timed out: {e}")
                except Exception as e:
                    logger.error(f"Error sending command: {e}")
                    
            except json.JSONDecodeError:
                logger.error("Invalid JSON parameters. Please check the format.")
            except Exception as e:
                logger.error(f"Error processing command: {e}")
                
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Input error: {e}")

async def main():
    bridge = FigmaBridge(WEBSOCKET_PORT)
    await bridge.connect()
    
    logger.info(f"WebSocket server started on port {WEBSOCKET_PORT}")
    logger.info("Waiting for client connection...")
    
    # Wait until a connection is established
    while True:
        if bridge.is_connected():
            logger.info("Client connection established! Server is ready.")
            break
        await asyncio.sleep(1)  # Check every second
    
    # Start user input handling
    try:
        await handle_user_input(bridge)
    except KeyboardInterrupt:
        logger.info("\nShutting down server...")
    finally:
        # Clean up
        if bridge.server:
            bridge.server.close()
            await bridge.server.wait_closed()

if __name__ == "__main__":
    asyncio.run(main())