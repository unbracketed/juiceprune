# Troubleshooting Guide

This guide helps you diagnose and resolve common issues when using Prunejuice.

## Installation Issues

### Python Version Compatibility

**Problem**: Installation fails with Python version errors.

**Solution**:
```bash
# Check Python version (requires 3.11+)
python --version

# Using uv (recommended)
uv python install 3.11
uv add prunejuice

# Or upgrade Python via your system package manager
```

### Missing Dependencies

**Problem**: `uv` or `git` not found.

**Solution**:
```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Verify git is available
git --version
```

## Project Initialization Issues

### Not a Git Repository

**Problem**: `prj init` fails with "not a git repository" error.

**Solution**:
```bash
# Initialize git repository first
git init

# Then initialize prunejuice
prj init
```

### Permission Denied

**Problem**: Cannot create `.prj` directory.

**Solution**:
```bash
# Check directory permissions
ls -la

# Ensure write permissions
chmod u+w .

# Or run as appropriate user
sudo chown $USER:$USER .
```

## Command Execution Issues

### Command Not Found

**Problem**: `prj run <command>` fails with "command not found".

**Solution**:
```bash
# List available commands
prj list-commands

# Check command file exists
ls .prj/commands/

# Verify YAML syntax
prj run <command> --dry-run
```

### Invalid YAML Syntax

**Problem**: YAML parsing errors when loading commands.

**Symptoms**:
```
Error: Invalid YAML syntax in command file
```

**Solution**:
```bash
# Validate YAML syntax
python -c "import yaml; yaml.safe_load(open('.prj/commands/my-command.yaml'))"

# Common YAML issues:
# - Incorrect indentation (use spaces, not tabs)
# - Missing quotes around strings with special characters
# - Incorrect list syntax
```

### Step Execution Failures

**Problem**: Individual steps fail during command execution.

**Debugging**:
```bash
# Run with verbose output
prj run <command> --verbose

# Use dry run to see what will execute
prj run <command> --dry-run

# Check step scripts exist
ls .prj/steps/
```

## Git Worktree Issues

### Worktree Creation Fails

**Problem**: Cannot create worktree for command.

**Common Causes**:
- Branch already exists
- Insufficient disk space
- Git repository corruption

**Solution**:
```bash
# Check existing worktrees
git worktree list

# Remove stale worktrees
git worktree prune

# Check available disk space
df -h

# Verify git repository health
git fsck
```

### Worktree Directory Conflicts

**Problem**: Worktree path already exists.

**Solution**:
```bash
# List active worktrees
prj worktree list

# Remove specific worktree
prj worktree remove <path>

# Clean up all inactive worktrees
git worktree prune
```

### Git Branch Issues

**Problem**: Cannot switch to specified branch.

**Solution**:
```bash
# Check if branch exists locally
git branch -a

# Fetch from remote
git fetch origin

# Create branch if it doesn't exist
git checkout -b <branch-name>
```

## Tmux Session Issues

### Tmux Not Available

**Problem**: Session creation fails because tmux is not installed.

**Solution**:
```bash
# Install tmux (macOS)
brew install tmux

# Install tmux (Ubuntu/Debian)
sudo apt-get install tmux

# Install tmux (CentOS/RHEL)
sudo yum install tmux

# Verify installation
tmux -V
```

### Session Name Conflicts

**Problem**: Cannot create session because name already exists.

**Solution**:
```bash
# List existing sessions
prj session list

# Kill specific session
prj session kill <session-name>

# Kill all prunejuice sessions
tmux list-sessions | grep prunejuice | cut -d: -f1 | xargs -I {} tmux kill-session -t {}
```

### Session Attachment Issues

**Problem**: Cannot attach to session.

**Solution**:
```bash
# Check if session exists
tmux list-sessions

# Force attach (detach other clients)
tmux attach-session -t <session-name> -d

# Create new session if needed
prj session create <task-name>
```

## Performance Issues

### Slow Command Execution

**Problem**: Commands take too long to execute.

**Debugging Steps**:
```bash
# Enable timing information
prj run <command> --verbose

# Check system resources
top
htop

# Monitor disk I/O
iostat 1

# Check network if using remote resources
ping <remote-host>
```

**Optimization**:
- Reduce command complexity
- Use parallel execution where possible
- Optimize step scripts
- Consider faster storage (SSD)

### High Memory Usage

**Problem**: Prunejuice consumes excessive memory.

**Solution**:
```bash
# Monitor memory usage
prj status --verbose

# Reduce parallel execution
# In .prj/config/project.yaml:
# execution:
#   max_parallel_steps: 2

# Clean up old artifacts
prj cleanup --artifacts
```

## Database Issues

### Corrupted Database

**Problem**: SQLite database corruption errors.

**Solution**:
```bash
# Backup current database
cp .prj/database.db .prj/database.db.backup

# Check database integrity
sqlite3 .prj/database.db "PRAGMA integrity_check;"

# Rebuild from backup if corrupted
rm .prj/database.db
prj init
```

### Database Lock Issues

**Problem**: "Database is locked" errors.

**Solution**:
```bash
# Check for zombie processes
ps aux | grep prunejuice

# Kill any hanging processes
killall prunejuice

# Remove lock file if it exists
rm .prj/database.db-wal .prj/database.db-shm
```

## Environment and Configuration Issues

### Environment Variable Problems

**Problem**: Environment variables not being recognized.

**Debugging**:
```bash
# Check current environment
prj run <command> --env-debug

# Verify .env file syntax
cat .prj/.env

# Test environment loading
env | grep PRUNEJUICE
```

### Configuration Override Issues

**Problem**: Configuration not being applied correctly.

**Solution**:
```bash
# Check configuration hierarchy
prj config show

# Verify file syntax
python -c "import yaml; print(yaml.safe_load(open('.prj/config/project.yaml')))"

# Check global config
cat ~/.config/prunejuice/config.yaml
```

## Error Message Reference

### Common Error Codes

| Exit Code | Meaning | Action |
|-----------|---------|---------|
| 1 | General error | Check command syntax and logs |
| 2 | Command not found | Verify command exists in `.prj/commands/` |
| 3 | Invalid configuration | Check YAML syntax and required fields |
| 4 | Git operation failed | Check git repository status |
| 5 | Session operation failed | Verify tmux availability |
| 6 | File system error | Check permissions and disk space |

### Common Error Messages

**"Command execution failed"**
- Check step scripts exist and are executable
- Verify all required arguments are provided
- Check environment variables and paths

**"Worktree already exists"**
- Use `git worktree list` to see existing worktrees
- Remove unused worktrees with `git worktree remove`

**"Session creation failed"**
- Verify tmux is installed and working
- Check for session name conflicts
- Ensure sufficient system resources

## Debug Mode

### Enabling Debug Output

```bash
# Environment variable
export PRUNEJUICE_LOG_LEVEL=DEBUG
prj run <command>

# Command-line flag
prj run <command> --debug

# Configuration file
# In .prj/config/project.yaml:
# logging:
#   level: DEBUG
```

### Debug Information Includes

- Step execution timing
- Environment variable resolution
- File system operations
- Git and tmux command execution
- Database queries
- Configuration loading

## Getting Help

### Log Files

Check these locations for detailed logs:
- `.prj/logs/prunejuice.log`
- Session logs in `.prj/artifacts/<command>/session.log`
- Step output in `.prj/artifacts/<command>/steps/`

### System Information

When reporting issues, include:
```bash
# Prunejuice version
prj --version

# System information
uname -a
python --version
git --version
tmux -V

# Configuration
prj config show

# Recent events
prj history --recent 10
```

### Community Resources

- GitHub Issues: Report bugs and feature requests
- Documentation: Check for updated troubleshooting guides
- Examples: Review template commands for patterns

## Prevention Best Practices

### Regular Maintenance

```bash
# Clean up old artifacts
prj cleanup --artifacts --older-than 30d

# Prune unused worktrees
git worktree prune

# Kill old sessions
prj session cleanup

# Update dependencies
uv sync --upgrade
```

### Configuration Validation

```bash
# Validate configuration files
prj config validate

# Test commands without execution
prj run <command> --dry-run

# Regular health checks
prj status --health-check
```

### Monitoring

```bash
# Check system resources before major operations
df -h && free -h

# Monitor long-running commands
prj run <command> --monitor

# Set up alerts for failures
prj config set alerts.on_failure email
```

This troubleshooting guide should help you quickly identify and resolve common issues. For persistent problems, enable debug mode and review the log files for detailed error information.