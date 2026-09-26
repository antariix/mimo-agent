# AGENTS.md — mimo-agent

Simple Python scripts collection. No build system, no tests, no CI.

## Commands

```bash
python scripts/hello.py
python scripts/sys_check.py       # requires: pip install psutil
python scripts/calculator.py              # modern GUI calculator (zero extra dependencies)
python scripts/create_desktop_shortcut.py  # creates desktop app shortcut with custom icon
```

## Structure

- `scripts/` — standalone Python scripts, entrypoints only
- `.mimocode/` — runtime files (`.cron-lock`); do not edit

## Notes

- No dependency manifest (`requirements.txt` etc.); install per-script deps manually (only `psutil`)
- No `.gitignore` exists
- `.mimocode/` contains auto-generated agent runtime state — not human-authored
- Repo has a single commit and one branch (`master`)
- Platform: Windows (PowerShell preferred for commands)
