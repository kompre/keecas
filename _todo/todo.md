# Todo List

## Current Tasks

Write your tasks here following this format:

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
1. **Feature Branch Creation**: Always work in dev branch or feature branches
   ```bash
   # If creating a new feature branch:
   git checkout dev
   git checkout -b feature/[task-name]
   ```

2. Move the proposal from `proposal/` to `pending/[task-name].md`
3. Update the file with implementation progress and activity summaries
4. Use the pending file for ongoing development updates
5. Write an executive summary after each major progress is complete, to the end of the file.
6. After editing the task.md open the file in the current IDE (VSCODE) for the user, presenting the changes.

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