# MCP server for Figma client

This is an (unofficial) MCP server to let LLM clients interact with [Figma's plugin API](https://www.figma.com/plugin-docs/).

This is a very early version, so only a small subset of functionality is exposed:

- object selection
- change fill/stroke color
- create basic shapes 
- export node to PNG.

Even these features aren't very robust, so it's not very reliable at this stage.

Please feel free to fork and submit PRs for improvements/features.

# Prequisites & installation

## Figma plugin

- node >= v20.18.1


```
git clone git@github.com:nmfisher/figma_mcp.git 
cd figma_mcp
pushd plugin && npm run build && popd
```

In Figma, right-click and `Plugins->Development->Import plugin from Manifest`, and select the manifest.json file at `figma_mcp/plugin/dist`.

The plugin won't connect to the MCP server immediately - this will happen automatically when your MCP client (e.g. Claude Desktop) tries to connect to the MCP server.

## MCP server

- uv from https://github.com/astral-sh/uv

```
pushd server && uv pip install --requirement pyproject.toml && popd
```


If you are using Claude Desktop, add the following to your `/Users/{username}/Library/Application Support/Claude/claude_desktop_config.json` file:
```
    "figma":{
        "command": "/path/to/figma_mcp/server/.venv/bin/python", 
        "args":["/path/to/figma_mcp/server/figma.py"],
        "enabled": true
    }
```

# Implementation

This uses websockets to create a connection between the MCP server and the Figma plugin. 

 

