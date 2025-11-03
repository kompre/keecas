# Todo List

## Current Tasks (user generated)

<!-- No active tasks -->

<!-- Tasks moved to proposal phase -->

**Tasks awaiting approval in `proposal/`**:
- [docs-review-pre-publish.md](proposal/docs-review-pre-publish.md) - Comprehensive pre-publication documentation review and correction (awaiting review)
- [refactor-formatters-singledispatch.md](proposal/refactor-formatters-singledispatch.md) - Refactor formatter system to use singledispatch pattern (awaiting review)
- [refactor-docstring-see-also-interlinks.md](proposal/refactor-docstring-see-also-interlinks.md) - Standardize "See Also" sections with quartodoc interlinks (awaiting review)
- [configurable-label-generation.md](proposal/configurable-label-generation.md) - Add config option for stable label generation strategies in show_eqn (awaiting review)

**Tasks in development (`pending/`)**:
<!-- No tasks currently in development -->

**Completed tasks**:
- [branch-protection-and-ci.md](completed/2025-10-24/branch-protection-and-ci.md) - Complete CI/CD pipeline with test and release workflows, branch protection guide, and comprehensive documentation (completed 2025-10-24)
- [programmatic-api-documentation.md](completed/2025-10-23/programmatic-api-documentation.md) - Automated API docs with quartodoc (completed 2025-10-23)
- [docstring-guidelines.md](completed/2025-10-23/docstring-guidelines.md) - Google-style docstring guidelines and validation (completed 2025-10-23)




## Instructions for Claude

### Proposal Phase
When you see a tasks:
1. Create a detailed proposal file in `_todo/proposal/[task-name].md`
2. Include the original objective from this file and eliminate the entry from `todo.md`
3. Break down the task into specific implementation steps
4. backward compatibility / breaking changes are not an issue because we're planning a major update (check pyproject.toml for version, we're on track for 1.0.0)
5. Wait for user review, comments, and approval 

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