# MkDocs Implementation Plan

## Overview
Integrate MkDocs with Material theme for comprehensive Prunejuice documentation, prioritizing command definition and usage with supporting sections on worktrees and sessions.

## Documentation Structure

```
docs/
├── index.md                    # Landing page - What is Prunejuice?
├── quickstart/
│   ├── new-project.md         # Starting fresh with Prunejuice
│   ├── existing-project.md    # Adding Prunejuice to existing project  
│   └── first-command.md       # Running your first command
├── guides/
│   ├── command-definition.md  # How to define commands (PRIMARY FOCUS)
│   ├── step-creation.md       # Creating reusable steps
│   ├── project-setup.md       # Project configuration
│   └── workflows.md           # Common development workflows
├── concepts/
│   ├── worktrees.md          # Git worktree integration
│   ├── sessions.md           # Tmux session management
│   └── architecture.md       # System architecture overview
├── reference/
│   ├── commands.md           # Complete CLI command reference
│   ├── config.md            # Configuration options
│   └── yaml-schema.md       # Command/Step YAML schemas
└── advanced/
    ├── custom-integrations.md
    ├── mcp-server.md
    └── troubleshooting.md
```

## Implementation Phases

### Phase 1: Foundation Setup (Steps 1-4)
```
1. Update pyproject.toml with docs dependencies group
2. Create mkdocs.yml with Material theme configuration  
3. Extend Makefile with docs commands
4. Test basic MkDocs build: make docs-install && make docs-serve
```

**Validation**: `make docs-serve` works without errors

### Phase 2: Structure Setup (Steps 5-8)
```
5. Create docs/ directory structure with all subdirectories
6. Create navigation configuration in mkdocs.yml
7. Add placeholder files for all documentation pages
8. Verify navigation and structure: make docs-serve
```

**Validation**: Navigation structure is intuitive and complete

### Phase 3: Core Content (Steps 9-12)
```
9. Write docs/index.md (landing page)
10. Create primary focus content: guides/command-definition.md
11. Create all three quickstart guides
12. Build command reference from template analysis
```

**Validation**: Primary user journeys are documented

### Phase 4: Supporting Content (Steps 13-15)
```
13. Migrate concepts pages (worktrees, sessions, architecture)
14. Complete reference documentation (config, yaml-schema)
15. Add advanced topics and troubleshooting
```

**Validation**: All major topics covered

### Phase 5: Polish (Steps 16-17)
```
16. Add cross-references and internal links
17. Final review, testing, and optimization
```

**Validation**: Ready for publication

## Key Configuration Files

### MkDocs Configuration (mkdocs.yml)
```yaml
site_name: Prunejuice Documentation
site_description: Parallel agentic coding workflow orchestrator
site_url: https://your-username.github.io/prunejuice/
repo_url: https://github.com/your-username/prunejuice
repo_name: your-username/prunejuice

theme:
  name: material
  features:
    - navigation.tabs
    - navigation.sections
    - navigation.expand
    - navigation.top
    - search.highlight
    - search.share
    - content.code.copy
  palette:
    - scheme: default
      primary: deep purple
      accent: purple
      toggle:
        icon: material/brightness-7
        name: Switch to dark mode
    - scheme: slate
      primary: deep purple
      accent: purple
      toggle:
        icon: material/brightness-4
        name: Switch to light mode

plugins:
  - search
  - awesome-pages

markdown_extensions:
  - pymdownx.highlight
  - pymdownx.superfences
  - pymdownx.tabbed:
      alternate_style: true
  - admonition
  - pymdownx.details
```

### Makefile Extensions
```makefile
# Documentation commands
docs-install:
	uv add --group docs mkdocs mkdocs-material mkdocs-awesome-pages-plugin

docs-serve:
	uv run mkdocs serve

docs-build:
	uv run mkdocs build

docs-clean:
	rm -rf site/

docs-deploy:
	uv run mkdocs gh-deploy

# Update dev-setup to include docs
dev-setup: install docs-install lint typecheck test
```

## Content Migration Strategy

### Primary Sources
- **guide.md**: SDLC Commands section (lines 60-95) -> command-definition.md
- **README.md**: Quick Start section -> quickstart guides
- **Template files**: `src/prunejuice/template_commands/` -> examples and reference

### Navigation Strategy
- **User Journey Flow**: Quickstart → Guides → Concepts → Reference → Advanced
- **Command Definition Priority**: Most prominent in guides section
- **Quick Access**: Reference section for experienced users

## Success Criteria
- Users can quickly understand command definition and usage
- Clear paths for new and existing project adoption
- Professional documentation suitable for open source project
- Easy maintenance and future updates

## Implementation Status
- [x] Phase 1: Foundation Setup (Steps 1-4) ✅ COMPLETED
- [x] Phase 2: Structure Setup (Steps 5-8) ✅ COMPLETED
- [x] Phase 3: Core Content (Steps 9-12) ✅ COMPLETED
- [x] Phase 4: Supporting Content (Steps 13-15) ✅ COMPLETED
- [x] Phase 5: Polish (Steps 16-17) ✅ COMPLETED

## Implementation Complete! 🎉

All phases have been successfully implemented:

### ✅ What Was Accomplished

**Infrastructure & Build System:**
- MkDocs with Material theme fully configured
- Complete Makefile integration with docs commands
- pyproject.toml updated with docs dependencies
- Verified build system works correctly

**Documentation Structure:**
- Complete directory structure with logical organization
- All 16 documentation pages created and populated
- Navigation configured and tested
- User-journey focused information architecture

**Comprehensive Content:**
- **Landing Page**: Professional introduction with clear navigation
- **Quickstart Guides**: 3 complete guides for different user scenarios
- **Primary Focus Content**: Comprehensive command definition guide
- **Core Concepts**: Deep dives into worktrees, sessions, and architecture
- **Reference Documentation**: Complete CLI reference, configuration, and YAML schemas
- **Advanced Topics**: Custom integrations, MCP server setup, and troubleshooting

**Polish & Navigation:**
- Cross-references and internal links throughout
- Consistent formatting and structure
- Material theme with search, code highlighting, and navigation features
- Professional appearance suitable for open source project

### 🚀 Ready for Use

The documentation is now ready for:
- Local development: `make docs-serve`
- Production builds: `make docs-build`
- Deployment: `make docs-deploy` (GitHub Pages)
- Team collaboration and contribution