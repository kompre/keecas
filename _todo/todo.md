# Todo List

## Current Tasks

Write your tasks here following this format:

### type annotation and docstring

Review the current codebase and add type annotation and docstring where missing. Add useful comment for each function. Proceed one file at a time (make list to check it off, so I can review the work). Some files have been updated recently, while others are old and messier. 

Do a check if the docstring provided are actually representing the underline function.

Avoid using the object `Union`, but prefer `type1 | type2 | type3` instead.


## Instructions for Claude

### Proposal Phase
When you see tasks marked as "New":
1. Create a detailed proposal file in `_todo/proposal/[task-name].md`
2. Include the original objective from this file
3. Break down the task into specific implementation steps
4. Wait for user review, comments, and approval 

<!-- user comment wil be displayed here -->

### Development Phase
When user approves a proposal:
1. Move the proposal from `proposal/` to `pending/[task-name].md`
2. Update the file with implementation progress and activity summaries
3. Use the pending file for ongoing development updates
4. Write an executive summary after each major progress is complete, to the end of the file. 
5. After editing the task.md open the file in the IDE for the user, presenting the changes.

### Completion Phase
When tasks are completed:
1. Move the file from `pending/` to `completed/YYYY-MM-DD/`
2. Update with final summary and insights
3. Mark the task as "Completed" in this todo.md file