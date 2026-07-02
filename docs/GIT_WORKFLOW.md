# Git Workflow

## Branches

### main
Stable branch. Always keep it runnable.

### feature branches
Use for new work.

Examples:
- feature/sprint1-foundation
- feature/financial-core
- feature/real-estate-core
- feature/ai-cfo

## Basic Commands

```bash
git checkout -b feature/name
git status
git add .
git commit -m "Message"
git push -u origin feature/name
```

## Rule
`main` must always run with:

```bash
streamlit run app.py
```
