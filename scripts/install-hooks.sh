#!/bin/bash
#
# Install Git hooks for automatic Quarto notebook rendering
#

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔧 Installing Git hooks...${NC}"

# Check if we're in a git repository
if [ ! -d ".git" ]; then
    echo -e "${RED}❌ Error: Not in a Git repository${NC}"
    echo -e "${RED}   Please run this script from the repository root${NC}"
    exit 1
fi

# Check if source hook exists
if [ ! -f "scripts/pre-commit" ]; then
    echo -e "${RED}❌ Error: scripts/pre-commit not found${NC}"
    echo -e "${RED}   Please run this script from the repository root${NC}"
    exit 1
fi

# Create hooks directory if it doesn't exist
mkdir -p .git/hooks

# Backup existing pre-commit hook if it exists
if [ -f ".git/hooks/pre-commit" ]; then
    echo -e "${YELLOW}⚠️  Existing pre-commit hook found${NC}"
    backup_file=".git/hooks/pre-commit.backup.$(date +%Y%m%d_%H%M%S)"
    cp ".git/hooks/pre-commit" "$backup_file"
    echo -e "${YELLOW}   Backed up to: $backup_file${NC}"
fi

# Copy the pre-commit hook
cp scripts/pre-commit .git/hooks/pre-commit

# Make it executable
chmod +x .git/hooks/pre-commit

echo -e "${GREEN}✅ Pre-commit hook installed successfully!${NC}"
echo ""
echo -e "${BLUE}📋 What this hook does:${NC}"
echo -e "  • Auto-fixes linting issues with Ruff (check + format)"
echo -e "  • Validates docstrings in changed Python files (src/*.py)"
echo -e "  • Detects when .ipynb files in examples/quarto_example/ are being committed"
echo -e "  • Automatically converts notebooks to QMD format"
echo -e "  • Renders notebooks to PDF and HTML with --execute flag"
echo -e "  • Adds generated files to the commit"
echo ""
echo -e "${BLUE}🎯 Usage:${NC}"
echo -e "  • Just commit notebooks normally: ${GREEN}git commit${NC}"
echo -e "  • The hook runs automatically before each commit"
echo -e "  • To skip the hook: ${YELLOW}git commit --no-verify${NC}"
echo ""
echo -e "${BLUE}✨ Requirements:${NC}"
echo -e "  • Quarto CLI must be installed and in PATH"
echo -e "  • Notebooks should be in the examples/quarto_example/ directory"
echo ""
echo -e "${GREEN}🎉 Setup complete! Try committing a notebook change.${NC}"