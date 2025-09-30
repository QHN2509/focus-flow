Steps to publish this repository to GitHub (example):

1. Create a new GitHub repository (on github.com) and copy the repo URL.

2. Locally, initialize git (if not already initialized) and push:

```powershell
# from project root
git init
git add .
git commit -m "Initial commit: FocusFlow"
# replace <repo-url> with the GitHub HTTPS or SSH URL
git branch -M main
git remote add origin <repo-url>
git push -u origin main
```

3. Create a release (optional):

```powershell
# tag and push
git tag -a v0.1.0 -m "Initial release"
git push origin v0.1.0
```

Notes:
- Ensure you do not commit sensitive local files. The `.gitignore` in this repo already excludes `.venv/`, `productivity_agent.db`, `models/`, `dataset_exports/`, and `archives/`.
- If you want me to create the repo and push for you, tell me the remote URL and whether to use HTTPS or SSH and I can prepare a script to run locally.
