# AGENTS.md

This repository packages two portable **Agent Skills**: `itr/` (a thin form router) and `itr2/`
(the AY 2026-27 ITR-2 final-return assembler).

## Installing these skills on request

When the user asks something like *"install this skill"*, *"set this up"*, or *"add this to my
agent"* after cloning, do the following:

1. Ask which agent to install for if it isn't obvious, and map to the target directory:
   - **VS Code Copilot** → `~/.agents/skills/`
   - **Claude Code** → `~/.claude/skills/`
   - **GitHub Copilot CLI** → `~/.copilot/skills/`
2. Install both folders with `python install.py <copilot|claude|copilot-cli>`. If Python is not
   available, copy `itr/` and `itr2/` directly.
3. Confirm the destination now contains `itr/SKILL.md` and `itr2/SKILL.md`, and tell the user to
   reload their agent so the skills are picked up.

Do **not** commit or move any of the user's tax documents; treat all `*.pdf`, `*.csv`, and
`tax_input*.json` in their working folders as sensitive.

## What the skill does

See [README.md](./README.md) and [itr2/SKILL.md](./itr2/SKILL.md).
