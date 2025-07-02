# Custom Integrations

Prunejuice provides extensive integration capabilities for connecting with external tools, services, and workflows. This guide covers how to create custom integrations and extend Prunejuice's functionality.

## Integration Architecture

### Native Python Approach

Prunejuice uses a native Python architecture that provides several integration points:

```python
# Integration interfaces
from prunejuice.integrations import PlumIntegration, PotsIntegration
from prunejuice.worktree_utils import GitWorktreeManager
from prunejuice.session_utils import TmuxManager, SessionLifecycleManager
```

### Integration Types

1. **Tool Integrations** - External command-line tools (git, tmux, gh, docker)
2. **Service Integrations** - Web APIs and remote services
3. **IDE Integrations** - Editor and development environment connections
4. **CI/CD Integrations** - Build and deployment pipeline connections
5. **MCP Server Integrations** - Model Context Protocol servers

## Built-in Integrations

### Git Worktree Integration

The `PlumIntegration` class provides native Git worktree management:

```python
from prunejuice.integrations.plum import PlumIntegration

# Create integration instance
plum = PlumIntegration()

# Create a new worktree
worktree_path = plum.create_worktree(
    project_path=Path("/path/to/project"),
    branch_name="feature-branch"
)

# List all worktrees
worktrees = plum.list_worktrees(project_path)

# Remove worktree when done
plum.remove_worktree(project_path, worktree_path)
```

### Tmux Session Integration

The `PotsIntegration` class manages tmux sessions:

```python
from prunejuice.integrations.pots import PotsIntegration

# Create integration instance
pots = PotsIntegration()

# Create a new session
session_name = pots.create_session(
    working_dir=Path("/path/to/worktree"),
    task_name="development"
)

# List all sessions
sessions = pots.list_sessions()

# Attach to session
pots.attach_session(session_name)
```

## Creating Custom Integrations

### Integration Class Template

```python
from pathlib import Path
from typing import Optional, List, Dict, Any
import logging

logger = logging.getLogger(__name__)

class CustomIntegration:
    """Template for creating custom integrations."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the integration with optional configuration."""
        self.config = config or {}
        self._initialized = False
    
    def initialize(self) -> bool:
        """Initialize the integration. Return True if successful."""
        try:
            # Perform initialization steps
            self._check_dependencies()
            self._setup_connection()
            self._initialized = True
            logger.info("Custom integration initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize integration: {e}")
            return False
    
    def is_available(self) -> bool:
        """Check if the integration is available and ready to use."""
        return self._initialized and self._check_external_dependencies()
    
    def _check_dependencies(self):
        """Check for required dependencies."""
        # Implement dependency checking
        pass
    
    def _setup_connection(self):
        """Set up connection to external service/tool."""
        # Implement connection setup
        pass
    
    def _check_external_dependencies(self) -> bool:
        """Check external tool availability."""
        # Implement external dependency checking
        return True
```

### GitHub Integration Example

```python
import subprocess
from typing import Optional, Dict, Any

class GitHubIntegration:
    """Integration with GitHub CLI and API."""
    
    def __init__(self, token: Optional[str] = None):
        self.token = token
        self._gh_available = None
    
    def is_available(self) -> bool:
        """Check if GitHub CLI is available."""
        if self._gh_available is None:
            try:
                subprocess.run(["gh", "--version"], 
                             capture_output=True, check=True)
                self._gh_available = True
            except (subprocess.CalledProcessError, FileNotFoundError):
                self._gh_available = False
        return self._gh_available
    
    def create_pr(self, title: str, body: str, 
                  base: str = "main") -> Dict[str, Any]:
        """Create a pull request."""
        if not self.is_available():
            raise RuntimeError("GitHub CLI not available")
        
        cmd = [
            "gh", "pr", "create",
            "--title", title,
            "--body", body,
            "--base", base
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"Failed to create PR: {result.stderr}")
        
        return {"url": result.stdout.strip()}
    
    def get_issue(self, issue_number: int) -> Dict[str, Any]:
        """Fetch issue details."""
        cmd = ["gh", "issue", "view", str(issue_number), "--json", "title,body,labels"]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"Failed to fetch issue: {result.stderr}")
        
        import json
        return json.loads(result.stdout)
```

### Docker Integration Example

```python
import docker
from typing import List, Dict, Any

class DockerIntegration:
    """Integration with Docker for containerized development."""
    
    def __init__(self):
        self.client = None
    
    def initialize(self) -> bool:
        """Initialize Docker client."""
        try:
            self.client = docker.from_env()
            self.client.ping()
            return True
        except Exception as e:
            logger.error(f"Docker not available: {e}")
            return False
    
    def run_container(self, image: str, command: str, 
                     volumes: Dict[str, str] = None) -> str:
        """Run a command in a container."""
        if not self.client:
            raise RuntimeError("Docker client not initialized")
        
        container = self.client.containers.run(
            image=image,
            command=command,
            volumes=volumes or {},
            detach=True,
            remove=True
        )
        
        return container.id
    
    def build_image(self, dockerfile_path: Path, tag: str) -> str:
        """Build a Docker image."""
        image, logs = self.client.images.build(
            path=str(dockerfile_path.parent),
            dockerfile=dockerfile_path.name,
            tag=tag
        )
        
        return image.id
```

## Command-Level Integration

### Using Integrations in Commands

Integrations can be used within command steps:

```yaml
# .prj/commands/deploy-with-docker.yaml
name: deploy-with-docker
description: Deploy application using Docker
category: deployment

arguments:
  - name: environment
    description: Target environment
    required: true
    type: string

steps:
  - name: build-image
    type: script
    script: |
      #!/bin/bash
      docker build -t myapp:${environment} .
  
  - name: deploy-container
    type: script
    script: |
      #!/bin/bash
      docker run -d --name myapp-${environment} myapp:${environment}

environment:
  DOCKER_BUILDKIT: "1"
```

### Custom Step Types

Create custom step types that use your integrations:

```python
# .prj/extensions/custom_steps.py
from prunejuice.core.executor import StepExecutor
from .integrations import GitHubIntegration

class GitHubStepExecutor(StepExecutor):
    """Custom step executor for GitHub operations."""
    
    def __init__(self):
        super().__init__()
        self.github = GitHubIntegration()
    
    def execute_github_pr(self, step_config: Dict[str, Any]) -> bool:
        """Execute GitHub PR creation step."""
        title = step_config.get("title")
        body = step_config.get("body")
        base = step_config.get("base", "main")
        
        try:
            result = self.github.create_pr(title, body, base)
            self.log_info(f"Created PR: {result['url']}")
            return True
        except Exception as e:
            self.log_error(f"Failed to create PR: {e}")
            return False
```

## IDE Integrations

### VS Code Integration

```python
import json
from pathlib import Path

class VSCodeIntegration:
    """Integration with Visual Studio Code."""
    
    def __init__(self, workspace_path: Path):
        self.workspace_path = workspace_path
        self.settings_path = workspace_path / ".vscode" / "settings.json"
    
    def setup_workspace(self, settings: Dict[str, Any]):
        """Configure VS Code workspace settings."""
        self.settings_path.parent.mkdir(exist_ok=True)
        
        existing_settings = {}
        if self.settings_path.exists():
            with open(self.settings_path) as f:
                existing_settings = json.load(f)
        
        # Merge settings
        existing_settings.update(settings)
        
        with open(self.settings_path, "w") as f:
            json.dump(existing_settings, f, indent=2)
    
    def add_task(self, task_name: str, command: str):
        """Add a task to VS Code tasks.json."""
        tasks_path = self.workspace_path / ".vscode" / "tasks.json"
        tasks_path.parent.mkdir(exist_ok=True)
        
        tasks = {"version": "2.0.0", "tasks": []}
        if tasks_path.exists():
            with open(tasks_path) as f:
                tasks = json.load(f)
        
        new_task = {
            "label": task_name,
            "type": "shell",
            "command": command,
            "group": "build"
        }
        
        tasks["tasks"].append(new_task)
        
        with open(tasks_path, "w") as f:
            json.dump(tasks, f, indent=2)
```

### Integration in Commands

```yaml
# .prj/commands/setup-vscode.yaml
name: setup-vscode
description: Configure VS Code workspace
category: development

steps:
  - name: setup-workspace
    type: script
    script: |
      python -c "
      from extensions.vscode_integration import VSCodeIntegration
      from pathlib import Path
      
      vscode = VSCodeIntegration(Path('.'))
      vscode.setup_workspace({
          'python.defaultInterpreterPath': './venv/bin/python',
          'python.linting.enabled': True,
          'python.linting.pylintEnabled': True
      })
      
      vscode.add_task('Run Tests', 'prj run test')
      vscode.add_task('Build Docs', 'prj run docs-build')
      "
```

## CI/CD Integrations

### GitHub Actions Integration

```python
from pathlib import Path
import yaml

class GitHubActionsIntegration:
    """Integration with GitHub Actions."""
    
    def __init__(self, project_path: Path):
        self.project_path = project_path
        self.workflows_path = project_path / ".github" / "workflows"
    
    def create_workflow(self, name: str, workflow_config: Dict[str, Any]):
        """Create a GitHub Actions workflow."""
        self.workflows_path.mkdir(parents=True, exist_ok=True)
        
        workflow_file = self.workflows_path / f"{name}.yml"
        with open(workflow_file, "w") as f:
            yaml.dump(workflow_config, f, default_flow_style=False)
    
    def create_prunejuice_workflow(self):
        """Create a workflow that uses Prunejuice commands."""
        workflow = {
            "name": "Prunejuice CI",
            "on": ["push", "pull_request"],
            "jobs": {
                "test": {
                    "runs-on": "ubuntu-latest",
                    "steps": [
                        {"uses": "actions/checkout@v3"},
                        {
                            "name": "Set up Python",
                            "uses": "actions/setup-python@v4",
                            "with": {"python-version": "3.11"}
                        },
                        {
                            "name": "Install uv",
                            "run": "pip install uv"
                        },
                        {
                            "name": "Install Prunejuice",
                            "run": "uv add prunejuice"
                        },
                        {
                            "name": "Initialize project",
                            "run": "prj init"
                        },
                        {
                            "name": "Run tests",
                            "run": "prj run test-ci"
                        }
                    ]
                }
            }
        }
        
        self.create_workflow("ci", workflow)
```

## MCP Server Integration

### Setting up MCP Server

Based on the guide.md mention of MCP server capabilities:

```python
from typing import List, Dict, Any
import asyncio

class MCPServerIntegration:
    """Integration for exposing Prunejuice commands via MCP server."""
    
    def __init__(self, project_path: Path):
        self.project_path = project_path
        self.available_commands = []
    
    async def start_server(self, port: int = 8000):
        """Start MCP server to expose commands as tools."""
        from prunejuice.commands.loader import ActionLoader
        
        # Load available commands
        loader = ActionLoader(self.project_path)
        self.available_commands = await loader.load_all_commands()
        
        # Start MCP server (implementation depends on MCP framework)
        # This would integrate with the MCP server framework
        pass
    
    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """Get tool definitions for MCP clients."""
        tools = []
        
        for command in self.available_commands:
            tool = {
                "name": f"prj_{command['name']}",
                "description": command.get("description", ""),
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
            
            # Add command arguments as tool parameters
            for arg in command.get("arguments", []):
                tool["parameters"]["properties"][arg["name"]] = {
                    "type": arg.get("type", "string"),
                    "description": arg.get("description", "")
                }
                
                if arg.get("required", False):
                    tool["parameters"]["required"].append(arg["name"])
            
            tools.append(tool)
        
        return tools
```

## Configuration and Environment

### Integration Configuration

```yaml
# .prj/config/integrations.yaml
integrations:
  github:
    enabled: true
    token_env: GITHUB_TOKEN
    default_base_branch: main
  
  docker:
    enabled: true
    registry: docker.io
    build_context: .
  
  vscode:
    enabled: true
    auto_setup: true
    workspace_settings:
      python.defaultInterpreterPath: ./venv/bin/python
  
  mcp_server:
    enabled: false
    port: 8000
    expose_all_commands: true
```

### Environment Variables

```bash
# Integration-specific environment variables
export GITHUB_TOKEN="your_github_token"
export DOCKER_REGISTRY="your_registry"
export PRUNEJUICE_INTEGRATIONS_CONFIG="/path/to/integrations.yaml"

# Integration feature flags
export PRUNEJUICE_ENABLE_GITHUB=true
export PRUNEJUICE_ENABLE_DOCKER=true
export PRUNEJUICE_ENABLE_MCP_SERVER=false
```

## Best Practices

### Error Handling

```python
class IntegrationError(Exception):
    """Base exception for integration errors."""
    pass

class IntegrationUnavailableError(IntegrationError):
    """Raised when an integration is not available."""
    pass

def safe_integration_call(integration_func, *args, **kwargs):
    """Safely call an integration function with error handling."""
    try:
        return integration_func(*args, **kwargs)
    except IntegrationUnavailableError:
        logger.warning(f"Integration not available: {integration_func.__name__}")
        return None
    except Exception as e:
        logger.error(f"Integration error in {integration_func.__name__}: {e}")
        raise
```

### Configuration Management

```python
from prunejuice.core.config import Settings

class IntegrationManager:
    """Manage all integrations for a project."""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.integrations = {}
    
    def load_integrations(self):
        """Load and initialize all configured integrations."""
        integration_config = self.settings.get("integrations", {})
        
        for name, config in integration_config.items():
            if config.get("enabled", False):
                try:
                    integration = self._create_integration(name, config)
                    if integration and integration.initialize():
                        self.integrations[name] = integration
                        logger.info(f"Loaded integration: {name}")
                except Exception as e:
                    logger.error(f"Failed to load integration {name}: {e}")
    
    def get_integration(self, name: str):
        """Get a specific integration by name."""
        return self.integrations.get(name)
```

### Testing Integrations

```python
import pytest
from unittest.mock import Mock, patch

class TestGitHubIntegration:
    """Test GitHub integration functionality."""
    
    def test_is_available_with_gh_cli(self):
        """Test availability when GitHub CLI is installed."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            
            integration = GitHubIntegration()
            assert integration.is_available() is True
    
    def test_create_pr_success(self):
        """Test successful PR creation."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = "https://github.com/user/repo/pull/123"
            
            integration = GitHubIntegration()
            result = integration.create_pr("Test PR", "Test body")
            
            assert result["url"] == "https://github.com/user/repo/pull/123"
```

## Security Considerations

### Token Management

- Store API tokens in environment variables, not in configuration files
- Use dedicated service accounts with minimal required permissions
- Rotate tokens regularly
- Never commit tokens to version control

### Network Security

- Use HTTPS for all API communications
- Validate SSL certificates
- Implement timeouts for external calls
- Consider using VPNs or private networks for sensitive integrations

### Access Control

- Implement proper authentication for MCP servers
- Use least-privilege principles for integration permissions
- Audit integration usage and access logs
- Implement rate limiting for external API calls

This guide provides a comprehensive foundation for creating custom integrations with Prunejuice. Start with the built-in integration patterns and extend them to meet your specific needs.