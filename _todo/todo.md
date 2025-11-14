# Todo List

## Current Tasks (user generated)

<!-- Tasks moved to proposal phase -->

**Tasks awaiting approval in `proposal/`**:
- [post-publication-marketing.md](proposal/post-publication-marketing.md) - Create marketing posts for Reddit, Quarto forums, and LinkedIn (awaiting platform-specific guidelines)
- [configurable-label-generation.md](proposal/configurable-label-generation.md) - Add config option for stable label generation strategies in show_eqn (awaiting review)

**Tasks in development (`pending/`)**:
- None currently

**Completed tasks** (most recent first):

### November 2025
- [fix-edit-double-browser-launch.md](completed/2025-11-14/fix-edit-double-browser-launch.md) - Fix double browser tab launch and add terminal link display (2025-11-14)
- [pre-release-ci-workflow-audit.md](completed/2025-11-12/pre-release-ci-workflow-audit.md) - Pre-release CI workflow audit (2025-11-12)
- [config-testing-phase2.md](completed/2025-11-12/config-testing-phase2.md) - Config Testing Phase 2: SKIPPED - 85% coverage already exists (2025-11-12)
- [config-generation-validation.md](completed/2025-11-12/config-generation-validation.md) - Config file generation validation and TOML comment syntax fixes (2025-11-12)
- [refactor-col-wrap-equals-sign.md](completed/2025-11-11/refactor-col-wrap-equals-sign.md) - Move `=` sign handling to col_wrap system using singledispatch (2025-11-11)
- [fix-update-pint-locale-naming.md](completed/2025-11-11/fix-update-pint-locale-naming.md) - Fix update_pint_locale naming (2025-11-11)
- [eliminate-config-shortcuts.md](completed/2025-11-11/eliminate-config-shortcuts.md) - Eliminate configuration property shortcuts for dot-notation consistency (2025-11-11)
- [docs-review-pre-publish.md](completed/2025-11-11/docs-review-pre-publish.md) - Comprehensive pre-publication documentation review (2025-11-11)
- [fix-pint-locale-config-access-bug.md](completed/2025-11-10/fix-pint-locale-config-access-bug.md) - Fix Pint locale config access bug (2025-11-10)
- [refactor-create-dataframe-singledispatch.md](completed/2025-11-06/refactor-create-dataframe-singledispatch.md) - Refactor create_dataframe using singledispatch (2025-11-06)
- [last-element-filler-pattern.md](completed/2025-11-05/last-element-filler-pattern.md) - Replace ambiguous tuple pattern with last-element-as-filler (2025-11-05)

### October 2025
- [refactor-formatters-singledispatch.md](completed/2025-10-30/refactor-formatters-singledispatch.md) - Refactor formatter system to use singledispatch (2025-10-30)
- [refactor-docstring-see-also-interlinks.md](completed/2025-10-30/refactor-docstring-see-also-interlinks.md) - Standardize "See Also" sections with quartodoc interlinks (2025-10-30)
- [branch-protection-and-ci.md](completed/2025-10-24/branch-protection-and-ci.md) - Complete CI/CD pipeline with test and release workflows (2025-10-24)
- [programmatic-api-documentation.md](completed/2025-10-23/programmatic-api-documentation.md) - Automated API docs with quartodoc (2025-10-23)
- [docstring-guidelines.md](completed/2025-10-23/docstring-guidelines.md) - Google-style docstring guidelines and validation (2025-10-23)
- [lazy-config-loading.md](completed/2025-10-06/lazy-config-loading.md) - Lazy config loading (2025-10-06)
- [refactor-pint-sympy.md](completed/2025-10-03/refactor-pint-sympy.md) - Refactor pint-sympy integration (2025-10-03)
- [fix-sympy-unit-scale-factors.md](completed/2025-10-03/fix-sympy-unit-scale-factors.md) - Fix SymPy unit scale factors (2025-10-03)
- [config-versioning-and-migration.md](completed/2025-10-03/config-versioning-and-migration.md) - Config versioning and migration system (2025-10-03)
- [cell-row-formatter-functions.md](completed/2025-10-03/cell-row-formatter-functions.md) - Cell/row formatter functions (2025-10-03)
- [latex-environment-templating.md](completed/2025-10-01/latex-environment-templating.md) - LaTeX environment templating (2025-10-01)
- [centralize-parameters-to-config.md](completed/2025-10-01/centralize-parameters-to-config.md) - Centralize parameters to config (2025-10-01)

### September 2025
- [type-annotation-and-docstring.md](completed/2025-09-25/type-annotation-and-docstring.md) - Type annotation and docstring improvements (2025-09-25)
- [localization-refactor.md](completed/2025-09-22/localization-refactor.md) - Localization refactor (2025-09-22)




## Instructions for Claude

### Proposal Phase
When you see a tasks:
1. Create a detailed proposal file in `_todo/proposal/[task-name].md`
2. Include the original objective from this file and eliminate the entry from `todo.md`
3. Break down the task into specific implementation steps
4. Wait for user review, comments, and approval 

<!-- user comment wil be displayed here -->

### Development Phase
When user approves a proposal:
1. commit and push
2. **Feature Branch Creation**: Always work in dev branch or feature branches
   ```bash
   # If creating a new feature branch:
   git checkout dev
   git checkout -b feature/[task-name]
   ```

3. Move the proposal from `proposal/` to `pending/[task-name].md`
4. Update the file with implementation progress and activity summaries
5. Use the pending file for ongoing development updates
6. Write an executive summary after each major progress is complete, to the end of the file.
7. After editing the task.md open the file in the current IDE (VSCODE) for the user, presenting the changes.

**Important**: Never use `git rm --cached` on proposal/pending files. Keep all `_todo/` files tracked normally. Feature branches should contain all proposals to avoid deletion on merge.

### Completion Phase
When tasks are completed:
1. Move the file from `pending/` to `completed/YYYY-MM-DD/`
2. Update with final summary and insights
3. Mark the task as "Completed" in this todo.md file

### Merge Phase
When merging a feature branch back to the base branch:
1. User will merge via GitHub PR interface
2. All `_todo/` files are preserved because they remain tracked in git
3. No special handling needed - standard git merge works correctly