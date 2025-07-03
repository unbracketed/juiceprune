"""Git status widget for displaying porcelain format git status."""

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional
from textual.reactive import reactive

from .base import BaseReactiveWidget


class PorcelainLineType(Enum):
    """Types of lines in git status --porcelain output."""
    BRANCH = "branch"
    STAGED = "staged"
    MODIFIED = "modified"
    UNTRACKED = "untracked"
    DELETED = "deleted"
    RENAMED = "renamed"
    COPIED = "copied"
    ADDED = "added"
    TYPECHANGE = "typechange"
    CLEAN = "clean"
    ERROR = "error"


@dataclass
class StatusLine:
    """Represents a single line in git status --porcelain output."""
    type: PorcelainLineType
    content: str
    file_path: Optional[str] = None
    index_status: Optional[str] = None
    worktree_status: Optional[str] = None


class PorcelainStatusParser:
    """Parses git status --porcelain --branch output into structured data."""
    
    @staticmethod
    def parse(status_output: str) -> List[StatusLine]:
        """Parse git status --porcelain --branch output into StatusLine objects."""
        if not status_output or status_output == "Working tree clean":
            return [StatusLine(PorcelainLineType.CLEAN, "Working tree clean")]
        
        if status_output.startswith("Git status error:") or status_output.startswith("Error getting git status:"):
            return [StatusLine(PorcelainLineType.ERROR, status_output)]
        
        lines = status_output.split('\n')
        parsed_lines = []
        
        for line in lines:
            if not line:
                continue
            
            # Branch information line (starts with ##)
            if line.startswith('##'):
                branch_info = line[3:]  # Remove '## ' prefix
                parsed_lines.append(StatusLine(
                    type=PorcelainLineType.BRANCH,
                    content=f"Branch: {branch_info}",
                    file_path=None
                ))
                continue
            
            # File status lines (XY filename format)
            if len(line) >= 3:
                index_status = line[0]
                worktree_status = line[1]
                file_path = line[3:]  # Skip the space
                
                # Determine the primary status type
                status_type = PorcelainStatusParser._determine_status_type(
                    index_status, worktree_status
                )
                
                # Create display content
                content = PorcelainStatusParser._format_status_line(
                    index_status, worktree_status, file_path
                )
                
                parsed_lines.append(StatusLine(
                    type=status_type,
                    content=content,
                    file_path=file_path,
                    index_status=index_status,
                    worktree_status=worktree_status
                ))
        
        return parsed_lines
    
    @staticmethod
    def _determine_status_type(index_status: str, worktree_status: str) -> PorcelainLineType:
        """Determine the primary status type from index and worktree status codes."""
        # Prioritize staged changes (index status)
        if index_status == 'A':
            return PorcelainLineType.ADDED
        elif index_status == 'M':
            return PorcelainLineType.STAGED
        elif index_status == 'D':
            return PorcelainLineType.DELETED
        elif index_status == 'R':
            return PorcelainLineType.RENAMED
        elif index_status == 'C':
            return PorcelainLineType.COPIED
        elif index_status == 'T':
            return PorcelainLineType.TYPECHANGE
        
        # Then check worktree status
        if worktree_status == 'M':
            return PorcelainLineType.MODIFIED
        elif worktree_status == 'D':
            return PorcelainLineType.DELETED
        elif worktree_status == 'T':
            return PorcelainLineType.TYPECHANGE
        elif worktree_status == '?':
            return PorcelainLineType.UNTRACKED
        
        # Default fallback
        return PorcelainLineType.MODIFIED
    
    @staticmethod
    def _format_status_line(index_status: str, worktree_status: str, file_path: str) -> str:
        """Format a status line for display."""
        status_map = {
            'A': 'new file',
            'M': 'modified',
            'D': 'deleted', 
            'R': 'renamed',
            'C': 'copied',
            'T': 'typechange'
        }
        
        parts = []
        
        # Handle special case of untracked files (both positions are ?)
        if index_status == '?' and worktree_status == '?':
            return f"  untracked: {file_path}"
        
        # Add index status if not space
        if index_status != ' ':
            index_desc = status_map.get(index_status, index_status)
            parts.append(f"staged {index_desc}")
        
        # Add worktree status if not space
        if worktree_status != ' ':
            worktree_desc = status_map.get(worktree_status, worktree_status)
            parts.append(f"unstaged {worktree_desc}")
        
        status_str = ", ".join(parts) if parts else "unknown"
        return f"  {status_str}: {file_path}"


class GitStatusWidget(BaseReactiveWidget):
    """Widget to display git status --porcelain output with colors."""
    
    git_status: reactive[str] = reactive("", recompose=True)
    
    def __init__(self, git_status: str = "", **kwargs) -> None:
        """Initialize the git status widget."""
        super().__init__(**kwargs)
        self.git_status = git_status
    
    def compose(self):
        """Compose the widget content."""
        from textual.widgets import Label
        
        if not self.git_status:
            yield Label(self.render_info("No git status available"))
            return
        
        # Parse the porcelain status
        status_lines = PorcelainStatusParser.parse(self.git_status)
        
        if not status_lines:
            yield Label(self.render_info("Working tree clean"))
            return
        
        # Render each status line
        for line in status_lines:
            rendered_content = self._render_status_line(line)
            yield Label(rendered_content)
    
    def _render_status_line(self, status_line: StatusLine) -> str:
        """Render a status line with appropriate colors."""
        content = status_line.content
        
        if status_line.type == PorcelainLineType.BRANCH:
            return f"[bold bright_blue]{content}[/]"
        elif status_line.type == PorcelainLineType.STAGED or status_line.type == PorcelainLineType.ADDED:
            return f"[bold green]{content}[/]"
        elif status_line.type == PorcelainLineType.MODIFIED:
            return f"[yellow]{content}[/]"
        elif status_line.type == PorcelainLineType.UNTRACKED:
            return f"[dim white]{content}[/]"
        elif status_line.type == PorcelainLineType.DELETED:
            return f"[red]{content}[/]"
        elif status_line.type == PorcelainLineType.RENAMED:
            return f"[cyan]{content}[/]"
        elif status_line.type == PorcelainLineType.COPIED:
            return f"[bright_cyan]{content}[/]"
        elif status_line.type == PorcelainLineType.TYPECHANGE:
            return f"[magenta]{content}[/]"
        elif status_line.type == PorcelainLineType.CLEAN:
            return f"[dim green]{content}[/]"
        elif status_line.type == PorcelainLineType.ERROR:
            return self.render_error(content)
        else:
            return f"[dim white]{content}[/]"
    
    def set_git_status(self, git_status: str) -> None:
        """Update the git status and trigger recomposition."""
        self.git_status = git_status