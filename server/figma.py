from typing import Any

import asyncio
import json
import websockets
from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server import NotificationOptions, Server
import mcp.server.stdio
from bridge import FigmaBridge

import logging

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

USER_AGENT = "figma-bridge/1.0"
WEBSOCKET_PORT = 8765

server = Server("figma")

# Global bridge instance (initialized in main)
bridge: FigmaBridge = None

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """
    List available tools.
    Each tool specifies its arguments using JSON Schema validation.
    """
    return [
        types.Tool(
            name="get-selection",
            description="Get information about the currently selected nodes",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
        types.Tool(
            name="get-selection-details",
            description="Get detailed information about selected nodes including children, constraints, and layout properties",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
        types.Tool(
            name="create-rectangle",
            description="Create a rectangle in Figma",
            inputSchema={
                "type": "object",
                "properties": {
                    "x": {
                        "type": "number",
                        "description": "X coordinate of the rectangle",
                    },
                    "y": {
                        "type": "number",
                        "description": "Y coordinate of the rectangle",
                    },
                },
                "required": [],
            },
        ),
        types.Tool(
            name="create-text",
            description="Create a text element in Figma",
            inputSchema={
                "type": "object",
                "properties": {
                    "x": {
                        "type": "number",
                        "description": "X coordinate of the text",
                    },
                    "y": {
                        "type": "number",
                        "description": "Y coordinate of the text",
                    },
                    "text": {
                        "type": "string",
                        "description": "Text content",
                    },
                },
                "required": [],
            },
        ),
        types.Tool(
            name="get-color-styles",
            description="Get a list of all color styles in the document",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
        types.Tool(
            name="create-color-style",
            description="Create or update a color style",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Name of the color style",
                    },
                    "color": {
                        "type": "object",
                        "description": "RGB color object",
                        "properties": {
                            "r": {"type": "number"},
                            "g": {"type": "number"},
                            "b": {"type": "number"},
                        },
                        "required": ["r", "g", "b"],
                    },
                },
                "required": ["name", "color"],
            },
        ),
        types.Tool(
            name="export-selection",
            description="Export the currently selected node",
            inputSchema={
                "type": "object",
                "properties": {
                    "format": {
                        "type": "string",
                        "description": "Export format (PNG, JPG, SVG, PDF)",
                    },
                    "scale": {
                        "type": "number",
                        "description": "Export scale (optional, default 1)",
                    },
                },
                "required": ["format"],
            },
        ),
        types.Tool(
            name="set-fill-color",
            description="Set fill color or gradient for the selected node",
            inputSchema={
                "type": "object",
                "properties": {
                    "value": {
                        "type": "object",
                        "description": "Color or gradient object",
                        "properties": {
                            "type": {
                                "type": "string",
                                "enum": [
                                    "SOLID",
                                    "GRADIENT_LINEAR",
                                    "GRADIENT_RADIAL",
                                    "GRADIENT_ANGULAR",
                                    "GRADIENT_DIAMOND",
                                ],
                                "description": "Specifies the type of value being provided.",
                            },
                            "color": {
                                "type": "object",
                                "properties": {
                                    "r": {
                                        "type": "number",
                                        "description": "Red component of the color (0-1)",
                                    },
                                    "g": {
                                        "type": "number",
                                        "description": "Green component of the color (0-1)",
                                    },
                                    "b": {
                                        "type": "number",
                                        "description": "Blue component of the color (0-1)",
                                    },
                                    "a": {
                                        "type": "number",
                                        "description": "Alpha component of the color (0-1, optional)",
                                        "default": 1,
                                    },
                                },
                                "required": ["r", "g", "b"],
                                "description": "Solid color definition (required when value.type is 'SOLID')",
                            },
                            "gradientStops": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "color": {
                                            "type": "object",
                                            "properties": {
                                                "r": {"type": "number"},
                                                "g": {"type": "number"},
                                                "b": {"type": "number"},
                                                "a": {"type": "number"},
                                            },
                                            "required": ["r", "g", "b", "a"],
                                        },
                                        "position": {"type": "number"},
                                    },
                                    "required": ["color", "position"],
                                },
                                "description": "Array of color stops (required for gradient types)",
                            },
                            "gradientTransform": {
                                "type": "array",
                                "items": {
                                    "type": "array",
                                    "items": {"type": "number"},
                                    "minItems": 3,
                                    "maxItems": 3,
                                },
                                "minItems": 2,
                                "maxItems": 2,
                                "description": "2x3 affine transformation matrix for the gradient",
                            },
                        },
                        "allOf": [
                            {
                                "if": {"properties": {"type": {"const": "SOLID"}}},
                                "then": {"required": ["color"]},
                            },
                            {
                                "if": {
                                    "properties": {"type": {"pattern": "^GRADIENT"}}
                                },
                                "then": {
                                    "required": ["gradientStops", "gradientTransform"]
                                },
                            },
                        ],
                    },
                    "styleId": {
                        "type": "string",
                        "description": "ID of the color style to apply (optional)",
                    },
                },
                "required": [],
                "anyOf": [{"required": ["value"]}, {"required": ["styleId"]}],
            },
        ),
        types.Tool(
            name="set-stroke-color",
            description="Set stroke color or gradient for the selected node",
            inputSchema={
                "type": "object",
                "properties": {
                    "value": {
                        "type": "object",
                        "description": "Color or gradient object",
                        "properties": {
                            "type": {
                                "type": "string",
                                "enum": [
                                    "SOLID",
                                    "GRADIENT_LINEAR",
                                    "GRADIENT_RADIAL",
                                    "GRADIENT_ANGULAR",
                                    "GRADIENT_DIAMOND",
                                ],
                                "description": "Specifies the type of value being provided.",
                            },
                            "color": {
                                "type": "object",
                                "properties": {
                                    "r": {
                                        "type": "number",
                                        "description": "Red component of the color (0-1)",
                                    },
                                    "g": {
                                        "type": "number",
                                        "description": "Green component of the color (0-1)",
                                    },
                                    "b": {
                                        "type": "number",
                                        "description": "Blue component of the color (0-1)",
                                    },
                                    "a": {
                                        "type": "number",
                                        "description": "Alpha component of the color (0-1, optional)",
                                        "default": 1,
                                    },
                                },
                                "required": ["r", "g", "b"],
                                "description": "Solid color definition (required when value.type is 'SOLID')",
                            },
                            "gradientStops": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "color": {
                                            "type": "object",
                                            "properties": {
                                                "r": {"type": "number"},
                                                "g": {"type": "number"},
                                                "b": {"type": "number"},
                                                "a": {"type": "number"},
                                            },
                                            "required": ["r", "g", "b", "a"],
                                        },
                                        "position": {"type": "number"},
                                    },
                                    "required": ["color", "position"],
                                },
                                "description": "Array of color stops (required for gradient types)",
                            },
                            "gradientTransform": {
                                "type": "array",
                                "items": {
                                    "type": "array",
                                    "items": {"type": "number"},
                                    "minItems": 3,
                                    "maxItems": 3,
                                },
                                "minItems": 2,
                                "maxItems": 2,
                                "description": "2x3 affine transformation matrix for the gradient",
                            },
                        },
                        "allOf": [
                            {
                                "if": {"properties": {"type": {"const": "SOLID"}}},
                                "then": {"required": ["color"]},
                            },
                            {
                                "if": {
                                    "properties": {"type": {"pattern": "^GRADIENT"}}
                                },
                                "then": {
                                    "required": ["gradientStops", "gradientTransform"]
                                },
                            },
                        ],
                    },
                    "styleId": {
                        "type": "string",
                        "description": "ID of the color style to apply (optional)",
                    },
                },
                "required": [],
                "anyOf": [{"required": ["value"]}, {"required": ["styleId"]}],
            },
        ),
        types.Tool(
            name="set-stroke-weight",
            description="Set stroke weight for the selected node",
            inputSchema={
                "type": "object",
                "properties": {
                    "value": {
                        "type": "number",
                        "description": "Stroke weight number",
                    },
                },
                "required": ["value"],
            },
        ),
        types.Tool(
            name="set-effect",
            description="Set effect for the selected node",
            inputSchema={
                "type": "object",
                "properties": {
                    "value": {
                        "type": "object",
                        "description": "Effect object",
                        "properties": {
                            "type": {
                                "type": "string",
                                "enum": [
                                    "INNER_SHADOW",
                                    "DROP_SHADOW",
                                    "LAYER_BLUR",
                                    "BACKGROUND_BLUR",
                                ],
                                "description": "Type of the effect",
                            },
                            "radius": {
                                "type": "number",
                                "description": "Radius of the effect",
                            },
                            "color": {
                                "type": "object",
                                "properties": {
                                    "r": {"type": "number"},
                                    "g": {"type": "number"},
                                    "b": {"type": "number"},
                                    "a": {"type": "number"},
                                },
                                "required": ["r", "g", "b", "a"],
                                "description": "Color of the effect (for shadow effects)",
                            },
                            "offset": {
                                "type": "object",
                                "properties": {
                                    "x": {"type": "number"},
                                    "y": {"type": "number"},
                                },
                                "required": ["x", "y"],
                                "description": "Offset of the effect (for shadow effects)",
                            },
                            "spread": {
                                "type": "number",
                                "description": "Spread of the shadow (for drop shadow effect)",
                            },
                            "visible": {"type": "boolean", "description": "Visibility of the effect"},
                            "blendMode": {
                                "type": "string",
                                "enum": [
                                    "NORMAL",
                                    "DARKEN",
                                    "MULTIPLY",
                                    "COLOR_BURN",
                                    "LIGHTEN",
                                    "SCREEN",
                                    "COLOR_DODGE",
                                    "OVERLAY",
                                    "SOFT_LIGHT",
                                    "HARD_LIGHT",
                                    "DIFFERENCE",
                                    "EXCLUSION",
                                    "HUE",
                                    "SATURATION",
                                    "COLOR",
                                    "LUMINOSITY",
                                ],
                                "description": "Blend mode of the effect (for shadow effects)",
                            },
                        },
                        "required": ["type", "radius"],
                        "allOf": [
                            {
                                "if": {
                                    "properties": {"type": {"enum": ["INNER_SHADOW", "DROP_SHADOW"]}}
                                },
                                "then": {
                                    "required": ["color", "offset", "blendMode"]
                                },
                            },
                            {
                                "if": {
                                    "properties": {"type": {"const": "DROP_SHADOW"}}
                                },
                                "then": {"required": ["spread"]},
                            },
                        ],
                    },
                },
                "required": ["value"],
            },
        ),
        types.Tool(
            name="figma-ping",
            description="Ping the Figma plugin to check its status",
            inputSchema={
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                        "description": "Message to send with the ping",
                    },
                    "timestamp": {
                        "type": "string",
                        "description": "Timestamp of the ping",
                    },
                },
                "required": [],
            },
        ),
    ]

@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict | None
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """
    Handle tool execution requests.
    Tools can create and manipulate Figma elements.
    """
    if not arguments:
        arguments = {}

    global bridge

    logger.info(f"Calling tool: {name} with arguments: {arguments} bridge is {bridge}")

    try:

        if bridge is None:
            logger.info("Creating figma bridge")
            bridge = FigmaBridge(WEBSOCKET_PORT)
            logger.info("Created figma bridge")
            await bridge.connect()
            await asyncio.sleep(5)  # Pause for 5 seconds
            logger.info("Connected")

        result = await bridge.send_command(name, arguments)
        logger.info(f"GOT TOOL RESULT : {result}")
        if name == "export-selection":
            return [types.ImageContent(type="image", data=result["data"])]
        else:
            return [types.TextContent(type="text", text=json.dumps(result))]

    except TimeoutError:
        logger.error("Timeout")
        return [
            types.TextContent(
                type="text",
                text="Operation timed out - ensure Figma plugin is connected",
            )
        ]
    except Exception as e:
        logger.error(e)
        return [
            types.TextContent(type="text", text=f"Failed to execute tool: {str(e)}")
        ]

async def main():
    # Run the MCP server using stdin/stdout streams
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="figma",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())