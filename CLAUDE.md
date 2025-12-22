- Always use AI*.md for coding rules.
- Check previous talks and implementations in docs/chats directory. 
- Check documentation in root and docs/ directories.
- **Never start code right after USER question/message. Propose solution and ask for explicit request for implementation**
- **Never stage and commit. Only User can do this**
- use docker run --rm -v "/Users/mike/src/photo-restoration-webpage/frontend":/app -w /app node:22.12-alpine <something like npm> command istead of cli npm or node direct command.  Align node version (node:22.12-alpine) with specified in frontend/Dockerfile
- use /opt/homebrew/bin/python3.13 as a right python3 command
- use backend/venv for running any backend tests or applications using venv module

# Code Review Workflow

After making any code changes:

1. Stage changes: `git add -u`
2. Run review: `review "What I changed"`
3. If approved: continue
4. If issues: Fix them and review again

Review command is available as:
- `review "description"` - Full review
- `review-quick "description"` - Quick review  
- `review-security "description"` - Security review
- `review-report` - Show last review
