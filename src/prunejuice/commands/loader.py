"""YAML command loader for PruneJuice."""

import yaml
from pathlib import Path
from typing import List, Optional, Dict, Any
import hashlib
import logging

from ..core.models import ActionDefintion, CommandArgument

logger = logging.getLogger(__name__)


class CommandLoader:
    """Loads and manages YAML command definitions."""

    def __init__(self):
        """Initialize command loader."""
        self._command_cache: Dict[str, ActionDefintion] = {}

    def discover_commands(self, project_path: Path) -> List[ActionDefintion]:
        """Discover all available commands in project and templates."""
        commands_by_name = {}

        # Project-specific commands (higher priority)
        project_cmd_dir = project_path / ".prj" / "commands"
        if project_cmd_dir.exists():
            project_commands = self._load_commands_from_dir(project_cmd_dir)
            for cmd in project_commands:
                commands_by_name[cmd.name] = cmd

        # Built-in template commands (lower priority)
        try:
            from importlib import resources

            template_files = resources.files("prunejuice.template_commands")
            for template_file in template_files.iterdir():
                if template_file.name.endswith(".yaml"):
                    try:
                        content = template_file.read_text()
                        cmd = self._parse_command_yaml(content, str(template_file))
                        if cmd and cmd.name not in commands_by_name:
                            commands_by_name[cmd.name] = cmd
                    except Exception as e:
                        logger.warning(
                            f"Failed to load template {template_file.name}: {e}"
                        )
        except Exception as e:
            logger.warning(f"Failed to load template commands: {e}")

        return list(commands_by_name.values())

    def load_command(
        self, command_name: str, project_path: Path
    ) -> Optional[ActionDefintion]:
        """Load a specific command by name."""
        # Check cache first
        if command_name in self._command_cache:
            return self._command_cache[command_name]

        # Look for command file
        search_paths = [
            project_path / ".prj" / "commands" / f"{command_name}.yaml",
            project_path / ".prj" / "commands" / f"{command_name}.yml",
        ]

        for cmd_path in search_paths:
            if cmd_path.exists():
                try:
                    with open(cmd_path, "r") as f:
                        content = f.read()

                    cmd = self._parse_command_yaml(content, str(cmd_path))
                    if cmd:
                        self._command_cache[command_name] = cmd
                        return cmd
                except Exception as e:
                    logger.error(f"Failed to load command {command_name}: {e}")

        # Try built-in templates
        try:
            from importlib import resources

            template_files = resources.files("prunejuice.template_commands")
            template_path = template_files / f"{command_name}.yaml"
            if template_path.is_file():
                content = template_path.read_text()
                cmd = self._parse_command_yaml(content, str(template_path))
                if cmd:
                    self._command_cache[command_name] = cmd
                    return cmd
        except Exception as e:
            logger.warning(f"Failed to load template command {command_name}: {e}")

        return None

    def _load_commands_from_dir(self, cmd_dir: Path) -> List[ActionDefintion]:
        """Load all commands from a directory."""
        commands = []

        for cmd_file in cmd_dir.glob("*.yaml"):
            try:
                with open(cmd_file, "r") as f:
                    content = f.read()

                cmd = self._parse_command_yaml(content, str(cmd_file))
                if cmd:
                    commands.append(cmd)
                    self._command_cache[cmd.name] = cmd
            except Exception as e:
                logger.error(f"Failed to load command from {cmd_file}: {e}")

        return commands

    def _parse_command_yaml(
        self, content: str, file_path: str
    ) -> Optional[ActionDefintion]:
        """Parse YAML content into ActionDefintion."""
        try:
            data = yaml.safe_load(content)
            if not data:
                return None

            # Handle command inheritance
            if data.get("extends"):
                base_data = self._resolve_base_command(data["extends"], file_path)
                if base_data:
                    # Merge base command data with current data
                    data = self._merge_command_data(base_data, data)

            # Parse arguments
            arguments = []
            for arg_data in data.get("arguments", []):
                if isinstance(arg_data, dict):
                    arguments.append(CommandArgument(**arg_data))
                elif isinstance(arg_data, str):
                    arguments.append(CommandArgument(name=arg_data))

            # Create command definition
            cmd = ActionDefintion(
                name=data["name"],
                description=data.get("description", ""),
                extends=data.get("extends"),
                category=data.get("category", "workflow"),
                arguments=arguments,
                environment=data.get("environment", {}),
                pre_steps=data.get("pre_steps", []),
                steps=data.get("steps", []),
                post_steps=data.get("post_steps", []),
                cleanup_on_failure=data.get("cleanup_on_failure", []),
                working_directory=data.get("working_directory"),
                timeout=data.get("timeout", 1800),
            )

            return cmd

        except yaml.YAMLError as e:
            logger.error(f"YAML parsing error in {file_path}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error parsing command from {file_path}: {e}")
            return None

    def _resolve_base_command(
        self, base_name: str, current_file: str
    ) -> Optional[Dict[str, Any]]:
        """Resolve base command data for inheritance."""
        try:
            # Look for base command in same directory as current file
            current_dir = Path(current_file).parent
            base_file = current_dir / f"{base_name}.yaml"

            if base_file.exists():
                with open(base_file, "r") as f:
                    return yaml.safe_load(f.read())
        except Exception as e:
            logger.warning(f"Could not resolve base command '{base_name}': {e}")

        return None

    def _merge_command_data(
        self, base_data: Dict[str, Any], derived_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Merge base command data with derived command data."""
        merged = base_data.copy()

        # Override simple fields
        for key in ["name", "description", "category", "working_directory", "timeout"]:
            if key in derived_data:
                merged[key] = derived_data[key]

        # Merge environment variables
        if "environment" in derived_data:
            base_env = merged.get("environment", {})
            derived_env = derived_data["environment"]
            merged["environment"] = {**base_env, **derived_env}

        # Merge lists (derived command extends base command)
        for list_key in [
            "pre_steps",
            "steps",
            "post_steps",
            "cleanup_on_failure",
            "arguments",
        ]:
            base_list = merged.get(list_key, [])
            derived_list = derived_data.get(list_key, [])
            merged[list_key] = base_list + derived_list

        return merged

    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate hash of a file for change detection."""
        with open(file_path, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()
