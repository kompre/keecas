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
1. **Optional Feature Branch Creation**: If user explicitly requests a new branch for the task:
   ```bash
   # Ensure dev branch is synced first
   git checkout dev
   git add . && git commit -m "sync: Commit pending changes"
   git push origin dev

   # Create feature branch
   git checkout -b feature/[task-name]

   # Remove other proposal files from tracking to keep branch focused
   git rm --cached _todo/proposal/other-task1.md
   git rm --cached _todo/proposal/other-task2.md
   # (remove all proposals except the one being worked on)

   # Commit the removal
   git commit -m "feat: Focus branch on [task-name] task only"

   # Also remove other pending tasks from tracking
   git rm --cached _todo/pending/other-pending-task.md
   git commit -m "feat: Remove other pending tasks from branch scope"

   # Clean workspace by removing untracked files to avoid confusion
   rm -rf _todo/proposal/  # Remove untracked proposal files
   rm _todo/pending/other-pending-task.md  # Remove untracked pending files
   ```
   If no explicit branch request, continue development in current active branch.

2. Move the proposal from `proposal/` to `pending/[task-name].md`
3. Update the file with implementation progress and activity summaries
4. Use the pending file for ongoing development updates
5. Write an executive summary after each major progress is complete, to the end of the file.
6. After editing the task.md open the file in the current IDE (VSCODE) for the user, presenting the changes.

### Completion Phase
When tasks are completed:
1. Move the file from `pending/` to `completed/YYYY-MM-DD/`
2. Update with final summary and insights
3. Mark the task as "Completed" in this todo.md file

### Merge Phase
When merging a feature branch back to the base branch:
1. **If feature branch was created**:
   ```bash
   # Switch to base branch (dev or main)
   git checkout dev

   # Merge the feature branch
   git merge feature/[task-name]

   # Delete the feature branch (optional cleanup)
   git branch -d feature/[task-name]
   git push origin --delete feature/[task-name]
   ```

2. **Important**: The `git rm --cached` approach ensures other proposal files are NOT deleted from the base branch during merge, as they were only untracked in the feature branch, not actually deleted.

3. Verify all proposal/pending files remain intact in `_todo/proposal/` or `_todo/pending/` after merge.