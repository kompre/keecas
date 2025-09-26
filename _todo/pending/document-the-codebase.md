# Document the Codebase

## Original Objective

I would like to create some comprehensive documentation of the codebase, so that a human can read and comprehend. Should at least be based on the docstring and dynamically updated when stuff change in the codebase. Optionally we could provide a general part where we describe the philosophy and the conventions of the package, based on the examples provided in `./examples/`.

Where this could be hosted? Can be hosted directly on github?

## Proposal

### Analysis

The codebase currently has:
- Comprehensive docstrings in most modules
- Convention documentation in `CLAUDE.md` (but targeted at Claude Code)
- Example notebooks in `examples/`
- Type annotations throughout the codebase
- Well-structured architecture

### Documentation Strategy

#### 1. Documentation Framework Choice
**Recommendation: Sphinx + GitHub Pages**
- **Sphinx**: Industry standard for Python documentation, supports autodoc for automatic docstring extraction
- **GitHub Pages**: Free hosting directly on GitHub, automatic deployment via GitHub Actions
- **Alternative**: MkDocs with Material theme (more modern look, simpler setup)

#### 2. Documentation Structure

```
docs/
├── source/
│   ├── index.rst                    # Main documentation page
│   ├── getting-started/
│   │   ├── installation.rst         # Installation guide
│   │   ├── quickstart.rst          # Quick tutorial
│   │   └── configuration.rst       # Configuration setup
│   ├── user-guide/
│   │   ├── conventions.rst         # Usage conventions and philosophy
│   │   ├── examples.rst            # Extended examples
│   │   ├── jupyter-integration.rst # Jupyter workflow
│   │   └── quarto-integration.rst  # Quarto workflow
│   ├── api-reference/
│   │   ├── display.rst             # Auto-generated from docstrings
│   │   ├── dataframe.rst           # Auto-generated from docstrings
│   │   ├── pipe-commands.rst       # Auto-generated from docstrings
│   │   ├── config.rst              # Auto-generated from docstrings
│   │   └── localization.rst        # Auto-generated from docstrings
│   ├── cli-reference/
│   │   └── commands.rst            # CLI documentation
│   └── developer-guide/
│       ├── contributing.rst        # Development setup
│       ├── architecture.rst        # Codebase architecture
│       └── testing.rst             # Testing guidelines
├── conf.py                         # Sphinx configuration
├── requirements.txt                # Documentation dependencies
└── make.bat / Makefile            # Build scripts
```

#### 3. Content Migration and Creation

**From existing sources:**
- Extract philosophy and conventions from `CLAUDE.md` → `user-guide/conventions.rst`
- Convert example notebooks → `user-guide/examples.rst` with executable examples
- CLI documentation from `--help` outputs → `cli-reference/commands.rst`
- Architecture overview from `CLAUDE.md` → `developer-guide/architecture.rst`

**New content to create:**
- Installation and quickstart guides
- Configuration documentation with TOML examples
- Jupyter/Quarto integration workflows
- Comprehensive API reference with examples

#### 4. Automation and Dynamic Updates

**Sphinx autodoc configuration:**
- Automatic docstring extraction from all modules
- Type hint integration for better API documentation
- Cross-references between functions and classes

**GitHub Actions workflow:**
- Trigger on pushes to main branch
- Build documentation with Sphinx
- Deploy to GitHub Pages
- Optional: Build on PR for preview

**Documentation maintenance:**
- Pre-commit hook to ensure docstrings are up-to-date
- Sphinx warnings for missing documentation
- Regular review of examples for accuracy

### Implementation Steps

#### Phase 1: Setup and Infrastructure
1. **Initialize Sphinx documentation**
   - Install Sphinx and required extensions
   - Create basic `conf.py` with autodoc configuration
   - Set up directory structure

2. **Configure GitHub Pages deployment**
   - Create GitHub Actions workflow
   - Configure repository settings for GitHub Pages
   - Test basic deployment

#### Phase 2: Content Migration
3. **Create user guide content**
   - Extract and adapt conventions from `CLAUDE.md`
   - Create installation and quickstart guides
   - Document configuration system with examples

4. **Generate API reference**
   - Configure autodoc for all modules
   - Add module-level documentation pages
   - Ensure cross-references work properly

#### Phase 3: Enhanced Documentation
5. **Add example integration**
   - Convert notebook examples to documentation format
   - Create step-by-step tutorials
   - Add Jupyter/Quarto workflow guides

6. **CLI and developer documentation**
   - Generate CLI reference from help output
   - Create developer/contributor guide
   - Add testing and architecture documentation

#### Phase 4: Automation and Polish
7. **Set up automation**
   - Configure pre-commit hooks for doc consistency
   - Test GitHub Actions deployment
   - Add documentation badges to README

8. **Review and polish**
   - Proofread all content
   - Ensure examples work correctly
   - Test navigation and cross-references

### Expected Outcomes

1. **Comprehensive Documentation Site**
   - Professional documentation hosted on GitHub Pages
   - Automatic updates when code changes
   - Easy navigation and search functionality

2. **Improved Developer Experience**
   - Clear API reference with examples
   - Step-by-step tutorials for common tasks
   - Documented conventions and best practices

3. **Better Maintainability**
   - Automatic docstring extraction prevents documentation drift
   - CI/CD integration ensures documentation stays current
   - Clear contribution guidelines for future development

### Timeline Estimate

- **Phase 1**: 1-2 days (setup and infrastructure)
- **Phase 2**: 2-3 days (content migration)
- **Phase 3**: 2-3 days (enhanced content)
- **Phase 4**: 1 day (automation and polish)

**Total**: ~6-9 days of development work

### Questions for User Review

1. **Framework preference**: Sphinx (more powerful, Python standard) vs. MkDocs (simpler, modern)?

<!-- let's use a modern and simpler look with Mkdocs -->

2. **Scope**: Should we include detailed mathematical theory or focus on practical usage?

<!-- only practical usage -->

3. **Examples**: How detailed should the example sections be? Include full engineering calculations?

<!-- at first we'll have simple example, jusy few code cell. More complex example could be added to a later date -->

4. **Audience**: Primary audience (researchers, engineers, students)?

<!-- this is aimed at engineers, maybe students -->

## Implementation Progress

**Status**: APPROVED - Implementation started
**Branch**: `feature/documentation-system`
**User Requirements**:
- Framework: MkDocs (modern and simpler look)
- Scope: Practical usage only (no detailed mathematical theory)
- Examples: Simple examples with few code cells initially
- Audience: Engineers and students

### Phase 1: Setup and Infrastructure (In Progress)

#### ✅ Completed
- [x] Created feature branch `feature/documentation-system`
- [x] Moved proposal to pending directory
- [x] Install MkDocs and Material theme
- [x] Create basic mkdocs.yml configuration
- [x] Set up directory structure
- [x] Create Getting Started section (installation, quickstart, configuration)
- [x] Create User Guide section (conventions, examples)
- [x] Test MkDocs build (successful)

#### 🔄 **PIVOT TO QUARTO** (User Request)
- [x] Switch from MkDocs to Quarto (better fit for Jupyter/scientific docs)
- [x] Create Quarto project structure
- [x] Convert existing content to .qmd format
- [x] Set up Quarto website configuration
- [x] Test Quarto preview server ✅ **WORKING**

#### ⏳ Next Steps
- [ ] Create remaining pages (installation, configuration, etc.)
- [ ] Add real Jupyter notebook examples
- [ ] Set up GitHub Actions for Quarto publishing
- [ ] Complete API Reference with quartodoc

#### 🚀 **CURRENT STATUS**
**Quarto documentation site is running!**
**Preview URL**: http://localhost:8080/
**Command**: `cd docs-qmd && quarto preview --port 8080`
