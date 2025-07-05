# Git-Layer Technical Q&A

## Git Operations & Behavior

### 1. Branch naming convention
**Q**: What naming pattern should transaction branches use? Should they include timestamps, UUIDs, or sequential IDs?
**A**: You decide.

### 2. Main branch name
**Q**: Should we assume "main" or "master", or should this be configurable/detected?
**A**: main

### 3. Clean working directory
**Q**: Should BEGIN fail if there are uncommitted changes, or should it stash them automatically?
**A**: No uncommitted changes on main. Write escalations create branches, even failed transactions preferably commit (unless something crashed). Generally write escalations - create a tmp clone for that transaction. On failure, commit too, but don't merge to main. Maintain main always tran committed state.

### 4. Nested transactions
**Q**: Should we support nested transactions, or should BEGIN fail if already in a transaction?
**A**: No nested.

### 5. Transaction isolation
**Q**: Since we're single-threaded, do we need any locking mechanism to prevent external Git operations during a transaction?
**A**: No.

### 6. Merge strategy
**Q**: For COMMIT, should we use regular merge, fast-forward only, or squash commits?
**A**: Regular.

### 7. Commit messages
**Q**: What should the automatic commit messages look like for transaction commits?
**A**: Up to you, maybe ai-db has to provide you that.

## Error Handling

### 8. Merge conflicts
**Q**: Even in single-threaded operation, conflicts could occur if external processes modify files. How should we handle this?
**A**: Answered above.

### 9. Git failures
**Q**: How should we handle Git command failures (e.g., corrupted repo, missing Git binary)?
**A**: Error.

### 10. Orphaned branches
**Q**: How should we clean up transaction branches from failed/abandoned transactions?
**A**: Think and decide best practice. But simple. If it's hard or not sure, maybe not needed for poc.

### 11. Recovery
**Q**: If the process crashes during a transaction, how should we recover on next startup?
**A**: Rely on git, maybe hard reset or smth. Generally should return to main.

## API Design

### 12. Transaction context
**Q**: Should transactions be managed via context managers, explicit handles, or global state?
**A**: Python with statement of those who use the library.

### 13. File operations
**Q**: Should the library provide file operation methods, or expect clients to use standard Python file I/O?
**A**: ai-db will use python standard io to files. To the folder you provide.

### 14. Transaction metadata
**Q**: Should we store any metadata about transactions (start time, operations performed, etc.)?
**A**: Maybe no. Just commit messages. Provided by ai-db. (well you'll manage files of frontend too). Generally, every successful operation inside a non-committed transaction should be a commit to a branch. Transaction commit = merge to main.

### 15. Status checking
**Q**: Should there be a method to check current transaction status?
**A**: No.

## Integration Concerns

### 16. Repository initialization
**Q**: Should the library auto-initialize a Git repo if none exists, or fail?
**A**: Yes, init.

### 17. Git configuration
**Q**: Any specific Git configs we should set (user.name, user.email, etc.)?
**A**: No.

### 18. Working directory
**Q**: Should we assume the current working directory is the repo root, or accept a path parameter?
**A**: A path parameter, mandatory, no default or fallback. Library config best practices in python.

### 19. Multiple repositories
**Q**: Should a single process be able to work with multiple repositories?
**A**: No, but why would your lib care? It could.

## Performance & Limitations

### 20. Large files
**Q**: Any special handling needed for large files or binary files?
**A**: No.

### 21. Transaction size limits
**Q**: Should we impose any limits on the number of operations per transaction?
**A**: No.

### 22. Performance monitoring
**Q**: Should we track/log transaction performance metrics?
**A**: No.

## Testing & Development

### 23. Test repository
**Q**: Should tests use temporary Git repos or a fixtures-based approach?
**A**: Decide.

### 24. Git version compatibility
**Q**: What's the minimum Git version we should support?
**A**: Can you use some git library? Not sure. Decide whats best practice in your case.

### 25. Dependencies
**Q**: Besides GitPython (or subprocess for Git commands), any other dependencies you prefer?
**A**: No, don't know.

## Key Implementation Decisions Based on Answers

### Transaction Model
- Write escalations trigger branch creation and use temporary clones
- Failed transactions still commit to their branch (but don't merge to main)
- Every successful operation within a transaction creates a commit
- Transaction commit = merge to main
- Main branch always stays in a clean, committed state

### API Model
- Context manager (with statement) for transaction management
- Path parameter is mandatory for repository location
- Clients use standard Python file I/O
- No transaction status checking method
- Commit messages provided by client (ai-db/ai-frontend)

### Error Handling
- Git failures raise errors
- Recovery relies on Git's built-in mechanisms (hard reset to main)
- No complex cleanup for orphaned branches (keep it simple for POC)