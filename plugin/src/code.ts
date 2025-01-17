figma.showUI(__html__, { width: 300, height: 200 });

interface CommandMessage {
  id: string;
  method: string;
  [key: string]: any;
}

// Helper function to get node properties
function getNodeProperties(node: SceneNode & BaseNode) {
  // Get shared properties available on all nodes
  const baseProperties: Record<string, any> = {
    id: node.id,
    type: node.type,
    name: node.name,
    visible: 'visible' in node ? node.visible : undefined,
    locked: 'locked' in node ? node.locked : undefined
  };

  // Add geometry properties if available
  if ('width' in node && 'height' in node) {
    baseProperties.width = node.width;
    baseProperties.height = node.height;
  }

  // Add position properties if available
  if ('x' in node && 'y' in node) {
    baseProperties.x = node.x;
    baseProperties.y = node.y;
  }

  // Add fill/stroke properties if available
  if ('fills' in node) {
    baseProperties.fills = node.fills;
  }

  if ('strokes' in node) {
    baseProperties.strokes = node.strokes;
    baseProperties.strokeWeight = node.strokeWeight;
  }

  return baseProperties;
}

// Function to create or update a color style
async function createOrUpdateColorStyle(name: string, color: RGB) {
  const existingStyles = figma.getLocalPaintStyles();
  const existingStyle = existingStyles.find((style) => style.name === name);

  if (existingStyle) {
    // Update existing style
    existingStyle.paints = [{ type: 'SOLID', color }];
    console.log('Updated existing color style:', name);
    return existingStyle;
  } else {
    // Create a new color style
    const newStyle = figma.createPaintStyle();
    newStyle.name = name;
    newStyle.paints = [{ type: 'SOLID', color }];
    console.log('Created new color style:', name);
    return newStyle;
  }
}

// Function to extract relevant information from a paint style
function extractPaintStyleInfo(style: PaintStyle) {
  return {
    id: style.id,
    name: style.name,
    description: style.description,
    paints: style.paints
  };
}

// Function to set fill color (SOLID)
function setFillColor(node: GeometryMixin, color: RGB) {
  const paints = Array.isArray(node.fills) ? Array.from(node.fills) : [];

  const solidPaint: SolidPaint = { type: 'SOLID', color };

  // Replace or add the solid paint
  if (paints.length > 0 && paints[0].type === 'SOLID') {
    paints[0] = solidPaint;
  } else {
    paints.unshift(solidPaint);
  }

  node.fills = paints;
}

// Function to set stroke color (SOLID)
function setStrokeColor(node: GeometryMixin, color: RGB) {
  const paints = Array.isArray(node.strokes) ? Array.from(node.strokes) : [];

  const solidPaint: SolidPaint = { type: 'SOLID', color };

  // Replace or add the solid paint
  if (paints.length > 0 && paints[0].type === 'SOLID') {
    paints[0] = solidPaint;
  } else {
    paints.unshift(solidPaint);
  }

  node.strokes = paints;
}

type GeometryBlendMixin = GeometryMixin & BlendMixin;

// Function to set fill gradient
function setFillGradient(node: GeometryMixin, gradient: GradientPaint) {
  const paints = Array.isArray(node.fills) ? Array.from(node.fills) : [];
  
  // Replace or add the gradient paint
  if (paints.length > 0 && paints[0].type.startsWith('GRADIENT')) {
    paints[0] = gradient;
  } else {
    paints.unshift(gradient);
  }

  node.fills = paints;
}

// Function to set stroke gradient
function setStrokeGradient(node: GeometryMixin, gradient: GradientPaint) {
  const paints = Array.isArray(node.strokes) ? Array.from(node.strokes) : [];

  // Replace or add the gradient paint
  if (paints.length > 0 && paints[0].type.startsWith('GRADIENT')) {
    paints[0] = gradient;
  } else {
    paints.unshift(gradient);
  }

  node.strokes = paints;
}

// Function to set stroke weight
function setStrokeWeight(node: GeometryMixin, strokeWeight: number) {
  node.strokeWeight = strokeWeight;
}

// Function to set effect (shadow, blur, etc.)
function setEffect(node: GeometryBlendMixin, effect: Effect) {
  const effects = node.effects ? [...node.effects] : [];
  effects.push(effect); // Add new effect to the list
  node.effects = effects;
}

// Function to apply a color style to a node's fill
function applyFillColorStyle(node: GeometryMixin, styleId: string) {
  const style = figma.getStyleById(styleId) as PaintStyle;
  if (!style) {
    throw new Error(`Color style with ID ${styleId} not found.`);
  }
  if (style.paints.length === 0) {
    throw new Error(`Color style ${style.name} has no paints defined.`);
  }

  node.fills = style.paints;
}

// Function to apply a color style to a node's stroke
function applyStrokeColorStyle(node: GeometryMixin, styleId: string) {
  const style = figma.getStyleById(styleId) as PaintStyle;
  if (!style) {
    throw new Error(`Color style with ID ${styleId} not found.`);
  }
  if (style.paints.length === 0) {
    throw new Error(`Color style ${style.name} has no paints defined.`);
  }

  node.strokes = style.paints;
}

// List of node types that support exportAsync
const exportableNodeTypes = [
  "BOOLEAN_OPERATION",
  "CODE_BLOCK",
  "COMPONENT",
  "COMPONENT_SET",
  "CONNECTOR",
  "ELLIPSE",
  "EMBED",
  "FRAME",
  "GROUP",
  "HIGHLIGHT",
  "INSTANCE",
  "LINE",
  "LINK_UNFURL",
  "MEDIA",
  "PAGE",
  "POLYGON",
  "RECTANGLE",
  "SECTION",
  "SHAPE_WITH_TEXT",
  "SLICE",
  "STAMP",
  "STAR",
  "STICKY",
  "TABLE",
  "TEXT",
  "VECTOR",
  "WASHI_TAPE",
  "WIDGET",
];

// Function to check if a node is exportable
function isExportable(node: SceneNode) {
  return exportableNodeTypes.includes(node.type);
}

// Handle commands from the UI
figma.ui.onmessage = async (msg: CommandMessage) => {
  const { method, id, ...params } = msg;
  console.log(method)
  console.log(params)
  let result;

  try {
    switch (method) {
      case 'get-selection':
        // Enhanced selection info
        result = figma.currentPage.selection.map(node => getNodeProperties(node));
        break;

      case 'get-selection-details':
        // Get detailed info about selected nodes including children
        result = figma.currentPage.selection.map(node => {
          const properties = getNodeProperties(node);
          
          // Add children info if the node is a container
          if ('children' in node) {
            properties['children'] = node.children.map(child => getNodeProperties(child));
          }
          
          // Add constraints if available
          if ('constraints' in node) {
            properties['constraints'] = node.constraints;
          }
          
          // Add layout properties if available
          if ('layoutMode' in node) {
            properties['layout'] = {
              layoutMode: node.layoutMode,
              primaryAxisAlignItems: node.primaryAxisAlignItems,
              counterAxisAlignItems: node.counterAxisAlignItems,
              paddingLeft: node.paddingLeft,
              paddingRight: node.paddingRight,
              paddingTop: node.paddingTop,
              paddingBottom: node.paddingBottom,
              itemSpacing: node.itemSpacing
            };
          }
          
          return properties;
        });
        break;
      case 'create-rectangle':
        const rect = figma.createRectangle();
        rect.x = params.x || figma.viewport.center.x;
        rect.y = params.y || figma.viewport.center.y;
        
        // Center viewport on the rectangle
        figma.viewport.scrollAndZoomIntoView([rect]);
        
        // Select the rectangle
        figma.currentPage.selection = [rect];
        
        result = { id: rect.id };
        break;

      case 'create-text':
        const text = figma.createText();
        text.x = params.x || figma.viewport.center.x;
        text.y = params.y || figma.viewport.center.y;
        text.characters = params.text || 'Hello World';
        
        // Center viewport on the text
        figma.viewport.scrollAndZoomIntoView([text]);
        
        // Select the text
        figma.currentPage.selection = [text];
        
        result = { id: text.id };
        break;

      case 'get-selection':
        result = figma.currentPage.selection.map(node => ({
          id: node.id,
          type: node.type,
          name: node.name
        }));
        break;

      case 'get-color-styles':
        const colorStyles = figma.getLocalPaintStyles();
        result = colorStyles.map(extractPaintStyleInfo);
        break;
  
      case 'create-color-style':
        // Create or update color style
        const { name, color } = params;
        if (!name || !color) {
          throw new Error("Name and color are required.");
        }
        const style = await createOrUpdateColorStyle(name, color);
        result = { styleId: style.id };
        break;

      case 'export-selection':
        if (figma.currentPage.selection.length === 0) {
          throw new Error("Please select a node to export.");
        }

        const selectedNode = figma.currentPage.selection[0];
        const { format, scale } = params;

        if (!format) {
          throw new Error("Format is required for exporting.");
        }

        // Check if the selected node is exportable
        if (!isExportable(selectedNode)) {
          throw new Error(`Node type ${selectedNode.type} is not exportable.`);
        }

        // Default scale to 1 if not provided
        const exportScale = scale || 1;

        let exportSettings: ExportSettings;
        switch (format.toUpperCase()) {
          case 'PNG':
            exportSettings = {
              format: 'PNG',
              constraint: { type: 'SCALE', value: exportScale }
            };
            break;
          case 'JPG':
            exportSettings = {
              format: 'JPG',
              constraint: { type: 'SCALE', value: exportScale }
            };
            break;
          case 'SVG':
            exportSettings = {
              format: 'SVG'
            };
            break;
          case 'PDF':
            exportSettings = {
              format: 'PDF'
            };
            break;
          default:
            throw new Error(`Unsupported export format: ${format}`);
        }

        const exportedData = await (selectedNode as any).exportAsync(exportSettings);
        result = { data: exportedData, format, scale: exportScale };
        
        break;
      
      case 'set-fill-color':
        if (figma.currentPage.selection.length === 0) {
          throw new Error("Please select a node to set fill color.");
        }

        const nodeToFill = figma.currentPage.selection[0] as GeometryMixin;
        const { value: fillColorValue, styleId: fillStyleId } = params;

        if (fillStyleId) {
          // Apply fill color style
          applyFillColorStyle(nodeToFill, fillStyleId);
        } else if (fillColorValue) {
          // Set fill color or gradient directly
          if (fillColorValue.type === 'SOLID') {
            setFillColor(nodeToFill, fillColorValue.color);
          } else if (fillColorValue.type.startsWith('GRADIENT')) {
            setFillGradient(nodeToFill, fillColorValue);
          } else {
            throw new Error(`Unsupported paint type for fills: ${fillColorValue.type}`);
          }
        } else {
          throw new Error("Either 'value' (color/gradient) or 'styleId' is required for setting fill color.");
        }

        result = { status: "Fill color set successfully." };
        break;

      case 'set-stroke-color':
        if (figma.currentPage.selection.length === 0) {
          throw new Error("Please select a node to set stroke color.");
        }

        const nodeToStroke = figma.currentPage.selection[0] as GeometryMixin;
        const { value: strokeColorValue, styleId: strokeStyleId } = params;

        if (strokeStyleId) {
          // Apply stroke color style
          applyStrokeColorStyle(nodeToStroke, strokeStyleId);
        } else if (strokeColorValue) {
          // Set stroke color or gradient directly
          if (strokeColorValue.type === 'SOLID') {
            setStrokeColor(nodeToStroke, strokeColorValue.color);
          } else if (strokeColorValue.type.startsWith('GRADIENT')) {
            setStrokeGradient(nodeToStroke, strokeColorValue);
          } else {
            throw new Error(`Unsupported paint type for strokes: ${strokeColorValue.type}`);
          }
        } else {
          throw new Error("Either 'value' (color/gradient) or 'styleId' is required for setting stroke color.");
        }

        result = { status: "Stroke color set successfully." };
        break;

      case 'set-stroke-weight':
        if (figma.currentPage.selection.length === 0) {
          throw new Error("Please select a node to set stroke weight.");
        }

        const nodeForStrokeWeight = figma.currentPage.selection[0] as GeometryMixin;
        const { value: strokeWeightValue } = params;

        if (typeof strokeWeightValue !== 'number') {
          throw new Error("'value' is required and must be a number for setting stroke weight.");
        }

        setStrokeWeight(nodeForStrokeWeight, strokeWeightValue);
        result = { status: "Stroke weight set successfully." };
        break;
      
      case 'set-effect':
        if (figma.currentPage.selection.length === 0) {
          throw new Error("Please select a node to set effect.");
        }

        const nodeForEffect = figma.currentPage.selection[0] as GeometryBlendMixin;
        const { value: effectValue } = params;

        if (!effectValue) {
          throw new Error("'value' (effect object) is required for setting an effect.");
        }
        setEffect(nodeForEffect, effectValue);
        result = { status: "Effect set successfully." };
        break;
  
      case 'figma-ping':
        // Respond to heartbeat with plugin status info
        result = {
          status: 'ok',
          timestamp: new Date().toISOString(),
          received_message: params.message,
          received_timestamp: params.timestamp,
          plugin_info: {
            version: '1.0.0',
            viewport: {
              zoom: figma.viewport.zoom,
              center: figma.viewport.center
            },
            current_page: {
              id: figma.currentPage.id,
              name: figma.currentPage.name,
              selection_count: figma.currentPage.selection.length
            }
          }
        };
        break;
      case 'list-functions':
        result = {
          functions: [
            {
              name: "get.selection",
              description: "Get information about the currently selected nodes",
              inputSchema: {
                type: "object",
                properties: {},
                required: [],
              },
            },
            {
              name: "get.selection.details",
              description: "Get detailed information about selected nodes including children, constraints, and layout properties",
              inputSchema: {
                type: "object",
                properties: {},
                required: [],
              },
            },
            {
              name: "create.rectangle",
              description: "Create a rectangle in Figma",
              inputSchema: {
                type: "object",
                properties: {
                  x: {
                    type: "number",
                    description: "X coordinate of the rectangle",
                  },
                  y: {
                    type: "number",
                    description: "Y coordinate of the rectangle",
                  },
                },
                required: [],
              },
            },
            {
              name: "create.text",
              description: "Create a text element in Figma",
              inputSchema: {
                type: "object",
                properties: {
                  x: {
                    type: "number",
                    description: "X coordinate of the text",
                  },
                  y: {
                    type: "number",
                    description: "Y coordinate of the text",
                  },
                  text: {
                    type: "string",
                    description: "Text content",
                  },
                },
                required: [],
              },
            },
            {
              name: "get.color.styles",
              description: "Get a list of all color styles in the document",
              inputSchema: {
                type: "object",
                properties: {},
                required: [],
              },
            },
            {
              name: "create.color.style",
              description: "Create or update a color style",
              inputSchema: {
                type: "object",
                properties: {
                  name: {
                    type: "string",
                    description: "Name of the color style",
                  },
                  color: {
                    type: "object",
                    description: "RGB color object",
                    properties: {
                      r: { type: "number" },
                      g: { type: "number" },
                      b: { type: "number" },
                    },
                    required: ["r", "g", "b"],
                  },
                },
                required: ["name", "color"],
              },
            },
            {
              name: "export.selection",
              description: "Export the currently selected node",
              inputSchema: {
                type: "object",
                properties: {
                  format: {
                    type: "string",
                    description: "Export format (PNG, JPG, SVG, PDF)",
                  },
                  scale: {
                    type: "number",
                    description: "Export scale (optional, default 1)",
                  },
                },
                required: ["format"],
              },
            },
            {
              name: "set.fill.color",
              description: "Set fill color or gradient for the selected node",
              inputSchema: {
                type: "object",
                properties: {
                  value: {
                    type: "object",
                    description: "Color or gradient object",
                  },
                  styleId: {
                    type: "string",
                    description: "ID of the color style to apply (optional)",
                  },
                },
                required: [],
              },
            },
            {
              name: "set.stroke.color",
              description: "Set stroke color or gradient for the selected node",
              inputSchema: {
                type: "object",
                properties: {
                  value: {
                    type: "object",
                    description: "Color or gradient object",
                  },
                  styleId: {
                    type: "string",
                    description: "ID of the color style to apply (optional)",
                  },
                },
                required: [],
              },
            },
            {
              name: "set.stroke.weight",
              description: "Set stroke weight for the selected node",
              inputSchema: {
                type: "object",
                properties: {
                  value: {
                    type: "number",
                    description: "Stroke weight number",
                  },
                },
                required: ["value"],
              },
            },
            {
              name: "set.effect",
              description: "Set effect for the selected node",
              inputSchema: {
                type: "object",
                properties: {
                  value: {
                    type: "object",
                    description: "Effect object",
                  },
                },
                required: ["value"],
              },
            },
            {
              name: "figma.ping",
              description: "Ping the Figma plugin to check its status",
              inputSchema: {
                type: "object",
                properties: {
                  message: {
                    type: "string",
                    description: "Message to send with the ping",
                  },
                  timestamp: {
                    type: "string",
                    description: "Timestamp of the ping",
                  },
                },
                required: [],
              },
            },
          ],
        };
        break;

      default:
        throw new Error(`Unknown command: ${method}`);
    }

    // Send result back to the UI
    figma.ui.postMessage({
      id,
      result
    });
  } catch (error) {
    console.error(`Error: ${error}`)
    figma.ui.postMessage({
      id,
      error: { "message": error instanceof Error ? error.message : String(error) }
    });
  }
};