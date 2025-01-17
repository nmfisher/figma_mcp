import asyncio
import json
import websockets
import time
import logging
from websockets.server import serve

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def start_websocket_server():
    """Starts the WebSocket server."""
    async with serve(handle_connection, "localhost", 8765):  # Pass the connection handler
        logging.info("WebSocket server started on ws://localhost:8765")
        await asyncio.Future()  # Keep the server running indefinitely

async def send_command(websocket, command):
    """Sends a command to the Figma plugin and waits for the response."""
    command_id = command["id"]
    logging.info(f"Sending command: {command_id} - {json.dumps(command)}")
    try:
        await websocket.send(json.dumps(command))
        response = await websocket.recv()
        logging.info(f"Received response for {command_id}: {response}")
        return json.loads(response)
    except Exception as e:
        logging.error(f"Error in send_command ({command_id}): {e}")
        raise

# Test functions
async def test_get_selection(websocket):
    """Tests the 'get-selection' method."""
    command = {"id": "test-get-selection", "method": "get-selection"}
    try:
        response = await send_command(websocket, command)
        assert "error" not in response, f"Error in get-selection: {response.get('error')}"
        assert "result" in response, "No result in get-selection response"
    except AssertionError as e:
        logging.error(f"Assertion failed in test_get_selection: {e}")
    except Exception as e:
        logging.error(f"Exception in test_get_selection: {e}")

async def test_get_selection_details(websocket):
    """Tests the 'get-selection-details' method."""
    command = {"id": "test-get-selection-details", "method": "get-selection-details"}
    try:
        response = await send_command(websocket, command)
        assert "error" not in response, f"Error in get-selection-details: {response.get('error')}"
        assert "result" in response, "No result in get-selection-details response"
    except AssertionError as e:
        logging.error(f"Assertion failed in test_get_selection_details: {e}")
    except Exception as e:
        logging.error(f"Exception in test_get_selection_details: {e}")

async def test_create_rectangle(websocket):
    """Tests the 'create-rectangle' method."""
    command = {"id": "test-create-rectangle", "method": "create-rectangle", "x": 100, "y": 100}
    try:
        response = await send_command(websocket, command)
        assert "error" not in response, f"Error in create-rectangle: {response.get('error')}"
        assert "result" in response and "id" in response["result"], "No rectangle ID in create-rectangle response"
    except AssertionError as e:
        logging.error(f"Assertion failed in test_create_rectangle: {e}")
    except Exception as e:
        logging.error(f"Exception in test_create_rectangle: {e}")

async def test_create_text(websocket):
    """Tests the 'create-text' method."""
    command = {"id": "test-create-text", "method": "create-text", "x": 200, "y": 200, "text": "Test Text"}
    try:
        response = await send_command(websocket, command)
        assert "error" not in response, f"Error in create-text: {response.get('error')}"
        assert "result" in response and "id" in response["result"], "No text ID in create-text response"
    except AssertionError as e:
        logging.error(f"Assertion failed in test_create_text: {e}")
    except Exception as e:
        logging.error(f"Exception in test_create_text: {e}")

async def test_get_color_styles(websocket):
    """Tests the 'get-color-styles' method."""
    command = {"id": "test-get-color-styles", "method": "get-color-styles"}
    try:
        response = await send_command(websocket, command)
        assert "error" not in response, f"Error in get-color-styles: {response.get('error')}"
        assert "result" in response, "No result in get-color-styles response"
    except AssertionError as e:
        logging.error(f"Assertion failed in test_get_color_styles: {e}")
    except Exception as e:
        logging.error(f"Exception in test_get_color_styles: {e}")

async def test_create_color_style(websocket):
    """Tests the 'create-color-style' method."""
    command = {"id": "test-create-color-style", "method": "create-color-style", "name": "Test Color Style", "color": {"r": 1, "g": 0, "b": 0}}
    try:
        response = await send_command(websocket, command)
        assert "error" not in response, f"Error in create-color-style: {response.get('error')}"
        assert "result" in response and "styleId" in response["result"], "No style ID in create-color-style response"
    except AssertionError as e:
        logging.error(f"Assertion failed in test_create_color_style: {e}")
    except Exception as e:
        logging.error(f"Exception in test_create_color_style: {e}")

async def test_export_selection(websocket):
    """Tests the 'export-selection' method (requires a node to be selected)."""
    # Assuming a node is already selected in Figma
    command = {"id": "test-export-selection", "method": "export-selection", "format": "PNG", "scale": 2}
    try:
        response = await send_command(websocket, command)
        assert "error" not in response, f"Error in export-selection: {response.get('error')}"
        assert "result" in response and "data" in response["result"], "No exported data in export-selection response"
    except AssertionError as e:
        logging.error(f"Assertion failed in test_export_selection: {e}")
    except Exception as e:
        logging.error(f"Exception in test_export_selection: {e}")

async def test_set_fill_color(websocket):
    """Tests the 'set-fill-color' method (requires a node to be selected)."""
    # Assuming a node is already selected in Figma
    command = {
        "id": "test-set-fill-color",
        "method": "set-fill-color",
        "value": {"type": "SOLID", "color": {"r": 0, "g": 1, "b": 0}}
    }
    try:
        response = await send_command(websocket, command)
        assert "error" not in response, f"Error in set-fill-color: {response.get('error')}"
        assert "result" in response and response["result"]["status"] == "Fill color set successfully.", "Failed to set fill color"
    except AssertionError as e:
        logging.error(f"Assertion failed in test_set_fill_color: {e}")
    except Exception as e:
        logging.error(f"Exception in test_set_fill_color: {e}")

async def test_set_stroke_color(websocket):
    """Tests the 'set-stroke-color' method (requires a node to be selected)."""
    # Assuming a node is already selected in Figma
    command = {
        "id": "test-set-stroke-color",
        "method": "set-stroke-color",
        "value": {"type": "SOLID", "color": {"r": 0, "g": 0, "b": 1}}
    }
    try:
        response = await send_command(websocket, command)
        assert "error" not in response, f"Error in set-stroke-color: {response.get('error')}"
        assert "result" in response and response["result"]["status"] == "Stroke color set successfully.", "Failed to set stroke color"
    except AssertionError as e:
        logging.error(f"Assertion failed in test_set_stroke_color: {e}")
    except Exception as e:
        logging.error(f"Exception in test_set_stroke_color: {e}")

async def test_set_stroke_weight(websocket):
    """Tests the 'set-stroke-weight' method (requires a node to be selected)."""
    # Assuming a node is already selected in Figma
    command = {
        "id": "test-set-stroke-weight",
        "method": "set-stroke-weight",
        "value": 5
    }
    try:
        response = await send_command(websocket, command)
        assert "error" not in response, f"Error in set-stroke-weight: {response.get('error')}"
        assert "result" in response and response["result"]["status"] == "Stroke weight set successfully.", "Failed to set stroke weight"
    except AssertionError as e:
        logging.error(f"Assertion failed in test_set_stroke_weight: {e}")
    except Exception as e:
        logging.error(f"Exception in test_set_stroke_weight: {e}")
        
async def test_set_effect(websocket):
    """Tests the 'set-effect' method (requires a node to be selected)."""
    # Assuming a node is already selected in Figma
    command = {
        "id": "test-set-effect",
        "method": "set-effect",
        "value": {"type": "DROP_SHADOW", "color": {"r": 0, "g": 0, "b": 0, "a": 0.5}, "offset": {"x": 5, "y": 5}, "radius": 10, "visible": True, "blendMode": "NORMAL"}
    }
    try:
        response = await send_command(websocket, command)
        assert "error" not in response, f"Error in set-effect: {response.get('error')}"
        assert "result" in response and response["result"]["status"] == "Effect set successfully.", "Failed to set effect"
    except AssertionError as e:
        logging.error(f"Assertion failed in test_set_effect: {e}")
    except Exception as e:
        logging.error(f"Exception in test_set_effect: {e}")

async def test_figma_ping(websocket):
    """Tests the 'figma-ping' method."""
    command = {"id": "test-figma-ping", "method": "figma-ping", "message": "Hello from Python!", "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ")}
    try:
        response = await send_command(websocket, command)
        assert "error" not in response, f"Error in figma-ping: {response.get('error')}"
        assert "result" in response and response["result"]["status"] == "ok", "figma-ping status is not 'ok'"
    except AssertionError as e:
        logging.error(f"Assertion failed in test_figma_ping: {e}")
    except Exception as e:
        logging.error(f"Exception in test_figma_ping: {e}")

async def test_list_functions(websocket):
    """Tests the 'list-functions' method."""
    command = {"id": "test-list-functions", "method": "list-functions"}
    try:
        response = await send_command(websocket, command)
        assert "error" not in response, f"Error in list-functions: {response.get('error')}"
        assert "result" in response and "functions" in response["result"], "No functions listed in list-functions response"
    except AssertionError as e:
        logging.error(f"Assertion failed in test_list_functions: {e}")
    except Exception as e:
        logging.error(f"Exception in test_list_functions: {e}")

async def run_all_tests(websocket):
    """Runs all test functions."""
    await test_get_selection(websocket)
    await test_get_selection_details(websocket)
    await test_create_rectangle(websocket)
    await test_create_text(websocket)
    await test_get_color_styles(websocket)
    await test_create_color_style(websocket)
    await test_export_selection(websocket)
    await test_set_fill_color(websocket)
    await test_set_stroke_color(websocket)
    await test_set_stroke_weight(websocket)
    await test_set_effect(websocket)
    await test_figma_ping(websocket)
    await test_list_functions(websocket)
    logging.info("All tests completed.")

async def handle_connection(websocket):
    """Handles incoming WebSocket connections and runs tests."""
    logging.info(f"Client connected: {websocket.remote_address}")
    try:
        await run_all_tests(websocket)
    except Exception as e:
        logging.error(f"Error during test execution: {e}")
    finally:
        logging.info(f"Client disconnected: {websocket.remote_address}")

async def main():
    """Starts the WebSocket server."""
    await start_websocket_server()

if __name__ == "__main__":
    asyncio.run(main())