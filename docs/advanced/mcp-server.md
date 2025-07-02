# MCP Server Setup

Model Context Protocol (MCP) allows Prunejuice to expose its commands as tools that can be used by AI assistants and other MCP-compatible clients. This guide covers how to set up and configure the MCP server functionality.

## Overview

The MCP server integration enables Prunejuice to:

- Expose project commands as MCP tools
- Allow AI assistants to execute Prunejuice commands
- Provide real-time access to project workflows
- Enable collaborative development with AI agents

As mentioned in the project guide, this allows for comprehensive lifecycle management with tools across requirement management, task management, architecture management, project monitoring, documentation export, and interactive interview capabilities.

## MCP Server Architecture

### Core Components

```
MCP Server
├── Tool Registry - Maps Prunejuice commands to MCP tools
├── Command Executor - Executes commands safely
├── Event Publisher - Publishes command events
├── Security Layer - Authentication and authorization
└── Client Manager - Manages connected clients
```

### Integration with Prunejuice

The MCP server integrates directly with Prunejuice's command system:

```python
from prunejuice.commands.loader import ActionLoader
from prunejuice.core.executor import CommandExecutor
from prunejuice.core.database import EventDatabase
```

## Installation and Setup

### Prerequisites

```bash
# Install MCP server dependencies
uv add "mcp-server>=1.0.0"
uv add "websockets>=10.0"
uv add "fastapi>=0.100.0"
uv add "uvicorn>=0.20.0"
```

### Basic Configuration

Add MCP server configuration to your project:

```yaml
# .prj/config/mcp-server.yaml
server:
  enabled: true
  host: "localhost"
  port: 8000
  protocol: "websocket"  # or "stdio"
  
security:
  authentication: true
  api_key_env: "PRUNEJUICE_MCP_API_KEY"
  allowed_clients: []  # Empty = allow all
  
tools:
  expose_all_commands: true
  exclude_commands: []
  include_templates: true
  
logging:
  level: "INFO"
  log_command_execution: true
```

### Environment Variables

```bash
# MCP server configuration
export PRUNEJUICE_MCP_ENABLED=true
export PRUNEJUICE_MCP_PORT=8000
export PRUNEJUICE_MCP_API_KEY="your-secure-api-key"

# Optional: Restrict client access
export PRUNEJUICE_MCP_ALLOWED_CLIENTS="client1,client2"
```

## Server Implementation

### Basic MCP Server

```python
# .prj/extensions/mcp_server.py
import asyncio
import json
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path

from prunejuice.commands.loader import ActionLoader
from prunejuice.core.executor import CommandExecutor
from prunejuice.core.config import Settings

logger = logging.getLogger(__name__)

class PrunejuiceMCPServer:
    """MCP server for exposing Prunejuice commands as tools."""
    
    def __init__(self, project_path: Path, settings: Settings):
        self.project_path = project_path
        self.settings = settings
        self.command_loader = ActionLoader(project_path)
        self.command_executor = CommandExecutor(project_path, settings)
        self.available_tools = {}
        self.connected_clients = set()
    
    async def initialize(self):
        """Initialize the MCP server."""
        # Load available commands
        commands = await self.command_loader.load_all_commands()
        
        # Convert commands to MCP tool definitions
        for command in commands:
            tool_def = self._create_tool_definition(command)
            self.available_tools[tool_def["name"]] = tool_def
        
        logger.info(f"Initialized MCP server with {len(self.available_tools)} tools")
    
    def _create_tool_definition(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """Convert a Prunejuice command to an MCP tool definition."""
        tool = {
            "name": f"prj_{command['name']}",
            "description": command.get("description", f"Execute {command['name']} command"),
            "inputSchema": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
        
        # Add command arguments as tool parameters
        for arg in command.get("arguments", []):
            tool["inputSchema"]["properties"][arg["name"]] = {
                "type": self._convert_type(arg.get("type", "string")),
                "description": arg.get("description", ""),
            }
            
            if arg.get("default") is not None:
                tool["inputSchema"]["properties"][arg["name"]]["default"] = arg["default"]
            
            if arg.get("required", False):
                tool["inputSchema"]["required"].append(arg["name"])
        
        return tool
    
    def _convert_type(self, prj_type: str) -> str:
        """Convert Prunejuice argument types to JSON Schema types."""
        type_mapping = {
            "string": "string",
            "integer": "integer",
            "float": "number",
            "boolean": "boolean",
            "list": "array",
            "dict": "object"
        }
        return type_mapping.get(prj_type, "string")
    
    async def handle_tool_call(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle a tool call from an MCP client."""
        try:
            # Validate tool exists
            if tool_name not in self.available_tools:
                return {
                    "error": f"Tool '{tool_name}' not found",
                    "available_tools": list(self.available_tools.keys())
                }
            
            # Extract command name from tool name
            command_name = tool_name.replace("prj_", "")
            
            # Execute the command
            result = await self.command_executor.execute_command(
                command_name=command_name,
                arguments=arguments,
                dry_run=False
            )
            
            return {
                "success": True,
                "result": result,
                "command": command_name,
                "arguments": arguments
            }
            
        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {e}")
            return {
                "error": str(e),
                "command": command_name,
                "arguments": arguments
            }
    
    async def get_available_tools(self) -> List[Dict[str, Any]]:
        """Get list of available tools."""
        return list(self.available_tools.values())
```

### WebSocket Server Implementation

```python
import websockets
import json
from websockets.server import serve

class MCPWebSocketServer:
    """WebSocket-based MCP server."""
    
    def __init__(self, mcp_server: PrunejuiceMCPServer):
        self.mcp_server = mcp_server
        
    async def handle_client(self, websocket, path):
        """Handle a new WebSocket client connection."""
        client_id = f"client_{id(websocket)}"
        self.mcp_server.connected_clients.add(client_id)
        
        logger.info(f"Client connected: {client_id}")
        
        try:
            # Send initial tools list
            tools = await self.mcp_server.get_available_tools()
            await websocket.send(json.dumps({
                "type": "tools_list",
                "tools": tools
            }))
            
            # Handle incoming messages
            async for message in websocket:
                try:
                    data = json.loads(message)
                    await self._handle_message(websocket, data)
                except json.JSONDecodeError:
                    await websocket.send(json.dumps({
                        "type": "error",
                        "message": "Invalid JSON"
                    }))
                except Exception as e:
                    await websocket.send(json.dumps({
                        "type": "error",
                        "message": str(e)
                    }))
        
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            self.mcp_server.connected_clients.discard(client_id)
            logger.info(f"Client disconnected: {client_id}")
    
    async def _handle_message(self, websocket, data: Dict[str, Any]):
        """Handle a message from a client."""
        message_type = data.get("type")
        
        if message_type == "tool_call":
            tool_name = data.get("tool_name")
            arguments = data.get("arguments", {})
            request_id = data.get("request_id")
            
            # Execute the tool
            result = await self.mcp_server.handle_tool_call(tool_name, arguments)
            
            # Send response
            response = {
                "type": "tool_response",
                "request_id": request_id,
                "result": result
            }
            await websocket.send(json.dumps(response))
        
        elif message_type == "get_tools":
            tools = await self.mcp_server.get_available_tools()
            response = {
                "type": "tools_list",
                "tools": tools
            }
            await websocket.send(json.dumps(response))
        
        else:
            await websocket.send(json.dumps({
                "type": "error",
                "message": f"Unknown message type: {message_type}"
            }))
    
    async def start_server(self, host: str = "localhost", port: int = 8000):
        """Start the WebSocket server."""
        logger.info(f"Starting MCP WebSocket server on {host}:{port}")
        
        async with serve(self.handle_client, host, port):
            await asyncio.Future()  # Run forever
```

## Command Integration

### Exposing Commands as Tools

Commands are automatically converted to MCP tools based on their YAML definitions:

```yaml
# .prj/commands/analyze-issue.yaml
name: analyze-issue
description: Analyze a Github Issue and make a plan to implement or resolve
category: analysis

arguments:
  - name: issue_number
    description: GitHub issue number to analyze
    type: integer
    required: true
  
  - name: repository
    description: Repository name (optional if configured)
    type: string
    required: false

steps:
  - name: fetch-issue
    type: builtin
    action: github_get_issue
  
  - name: analyze-requirements
    type: script
    script: analyze-issue-requirements.sh
  
  - name: create-implementation-plan
    type: script
    script: create-implementation-plan.sh
```

This becomes an MCP tool:

```json
{
  "name": "prj_analyze_issue",
  "description": "Analyze a Github Issue and make a plan to implement or resolve",
  "inputSchema": {
    "type": "object",
    "properties": {
      "issue_number": {
        "type": "integer",
        "description": "GitHub issue number to analyze"
      },
      "repository": {
        "type": "string",
        "description": "Repository name (optional if configured)"
      }
    },
    "required": ["issue_number"]
  }
}
```

### Command Execution Flow

1. **Client Request**: MCP client calls `prj_analyze_issue` tool
2. **Validation**: Server validates tool name and arguments
3. **Command Mapping**: Maps tool call to `analyze-issue` command
4. **Execution**: Executes command using CommandExecutor
5. **Response**: Returns execution results to client

## Client Integration

### Claude Code Integration

Configure Claude Code to use the MCP server:

```json
{
  "mcpServers": {
    "prunejuice": {
      "command": "uv",
      "args": ["run", "python", "-m", "prunejuice.mcp_server"],
      "cwd": "/path/to/your/project"
    }
  }
}
```

### Direct WebSocket Client

```python
import asyncio
import websockets
import json

async def example_client():
    """Example MCP client using WebSocket."""
    
    uri = "ws://localhost:8000"
    
    async with websockets.connect(uri) as websocket:
        # Get available tools
        await websocket.send(json.dumps({
            "type": "get_tools"
        }))
        
        response = await websocket.recv()
        tools = json.loads(response)
        print("Available tools:", [tool["name"] for tool in tools["tools"]])
        
        # Call a tool
        await websocket.send(json.dumps({
            "type": "tool_call",
            "tool_name": "prj_analyze_issue",
            "arguments": {
                "issue_number": 123,
                "repository": "myorg/myrepo"
            },
            "request_id": "req_001"
        }))
        
        # Wait for response
        response = await websocket.recv()
        result = json.loads(response)
        print("Tool result:", result)

# Run the client
asyncio.run(example_client())
```

## Security Configuration

### Authentication

```python
class MCPAuthenticator:
    """Handle MCP server authentication."""
    
    def __init__(self, api_key: str, allowed_clients: List[str] = None):
        self.api_key = api_key
        self.allowed_clients = set(allowed_clients or [])
    
    def authenticate(self, headers: Dict[str, str]) -> bool:
        """Authenticate a client request."""
        # Check API key
        provided_key = headers.get("Authorization", "").replace("Bearer ", "")
        if provided_key != self.api_key:
            return False
        
        # Check client allowlist if configured
        if self.allowed_clients:
            client_id = headers.get("X-Client-ID")
            if client_id not in self.allowed_clients:
                return False
        
        return True
```

### Rate Limiting

```python
import time
from collections import defaultdict

class RateLimiter:
    """Rate limiting for MCP server."""
    
    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.client_requests = defaultdict(list)
    
    def is_allowed(self, client_id: str) -> bool:
        """Check if client is within rate limits."""
        now = time.time()
        window_start = now - self.window_seconds
        
        # Clean old requests
        self.client_requests[client_id] = [
            req_time for req_time in self.client_requests[client_id]
            if req_time > window_start
        ]
        
        # Check limit
        if len(self.client_requests[client_id]) >= self.max_requests:
            return False
        
        # Record this request
        self.client_requests[client_id].append(now)
        return True
```

## Deployment

### Standalone Server

```python
# scripts/start_mcp_server.py
import asyncio
import logging
from pathlib import Path
from prunejuice.core.config import Settings
from extensions.mcp_server import PrunejuiceMCPServer, MCPWebSocketServer

async def main():
    """Start the MCP server."""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Load configuration
    project_path = Path.cwd()
    settings = Settings()
    
    # Initialize MCP server
    mcp_server = PrunejuiceMCPServer(project_path, settings)
    await mcp_server.initialize()
    
    # Start WebSocket server
    ws_server = MCPWebSocketServer(mcp_server)
    await ws_server.start_server(
        host=settings.mcp_host,
        port=settings.mcp_port
    )

if __name__ == "__main__":
    asyncio.run(main())
```

### Docker Deployment

```dockerfile
# Dockerfile.mcp-server
FROM python:3.11-slim

WORKDIR /app

# Install uv
RUN pip install uv

# Copy project files
COPY . .

# Install dependencies
RUN uv sync --locked

# Expose MCP server port
EXPOSE 8000

# Start the MCP server
CMD ["uv", "run", "python", "scripts/start_mcp_server.py"]
```

### Systemd Service

```ini
# /etc/systemd/system/prunejuice-mcp.service
[Unit]
Description=Prunejuice MCP Server
After=network.target

[Service]
Type=simple
User=prunejuice
WorkingDirectory=/opt/prunejuice-project
Environment=PRUNEJUICE_MCP_ENABLED=true
Environment=PRUNEJUICE_MCP_PORT=8000
ExecStart=/usr/local/bin/uv run python scripts/start_mcp_server.py
Restart=always

[Install]
WantedBy=multi-user.target
```

## Monitoring and Logging

### Command Execution Logging

```python
class MCPExecutionLogger:
    """Log MCP command executions."""
    
    def __init__(self, database_path: Path):
        self.db = EventDatabase(database_path)
    
    async def log_tool_call(self, client_id: str, tool_name: str, 
                           arguments: Dict[str, Any], result: Dict[str, Any]):
        """Log a tool call execution."""
        event_data = {
            "event_type": "mcp_tool_call",
            "client_id": client_id,
            "tool_name": tool_name,
            "arguments": arguments,
            "success": result.get("success", False),
            "execution_time": result.get("execution_time"),
            "error": result.get("error")
        }
        
        await self.db.log_event("mcp_server", event_data)
```

### Metrics Collection

```python
import time
from dataclasses import dataclass
from typing import Dict

@dataclass
class MCPMetrics:
    """MCP server metrics."""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    active_clients: int = 0
    average_response_time: float = 0.0
    tool_usage: Dict[str, int] = None
    
    def __post_init__(self):
        if self.tool_usage is None:
            self.tool_usage = {}

class MCPMetricsCollector:
    """Collect MCP server metrics."""
    
    def __init__(self):
        self.metrics = MCPMetrics()
        self.response_times = []
    
    def record_request(self, success: bool, response_time: float, tool_name: str):
        """Record a request for metrics."""
        self.metrics.total_requests += 1
        
        if success:
            self.metrics.successful_requests += 1
        else:
            self.metrics.failed_requests += 1
        
        self.response_times.append(response_time)
        if len(self.response_times) > 1000:  # Keep last 1000
            self.response_times = self.response_times[-1000:]
        
        self.metrics.average_response_time = sum(self.response_times) / len(self.response_times)
        
        # Track tool usage
        self.metrics.tool_usage[tool_name] = self.metrics.tool_usage.get(tool_name, 0) + 1
    
    def get_metrics(self) -> MCPMetrics:
        """Get current metrics."""
        return self.metrics
```

## Troubleshooting

### Common Issues

**Server Won't Start**
- Check if port is already in use: `lsof -i :8000`
- Verify Prunejuice is properly initialized: `prj status`
- Check configuration file syntax

**Tools Not Appearing**
- Verify commands are properly defined in `.prj/commands/`
- Check command YAML syntax: `prj list-commands`
- Ensure MCP server has loaded commands: check logs

**Authentication Failures**
- Verify API key is set correctly
- Check client authentication headers
- Review allowed clients configuration

**Command Execution Fails**
- Test commands directly: `prj run <command> --dry-run`
- Check command dependencies and environment
- Review execution logs and error messages

### Debug Mode

```bash
# Enable debug logging
export PRUNEJUICE_LOG_LEVEL=DEBUG
export PRUNEJUICE_MCP_DEBUG=true

# Start server with debug output
uv run python scripts/start_mcp_server.py --debug
```

The MCP server provides a powerful way to integrate Prunejuice with AI assistants and other development tools, enabling collaborative workflows and automated development processes.