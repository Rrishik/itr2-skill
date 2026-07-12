# AGENTS.md

This repository packages a portable **Agent Skill**: `itr2/` (an ITR-2 capital-gains
computation assistant for Indian income-tax filing).

## Installing this skill on request

When the user asks something like *"install this skill"*, *"set this up"*, or *"add this to my
agent"* after cloning, do the following:

1. Ask which agent to install for if it isn't obvious, and map to the target directory:
   - **VS Code Copilot** → `~/.agents/skills/`
   - **Claude Code** → `~/.claude/skills/`
   - **GitHub Copilot CLI** → `~/.copilot/skills/`
2. Copy the `itr2/` folder (this repo's skill folder) into that directory. Prefer the
   bundled helper if the environment can run it:
   - PowerShell: `./install.ps1 <copilot|claude|copilot-cli>`
   - bash: `./install.sh <copilot|claude|copilot-cli>`
   Otherwise copy the folder directly (`Copy-Item` / `cp -r`).
3. Confirm the destination now contains `itr2/SKILL.md`, and tell the user to reload
   their agent so the skill is picked up.

Do **not** commit or move any of the user's tax documents; treat all `*.pdf`, `*.csv`, and
`tax_input*.json` in their working folders as sensitive.

## What the skill does

See [README.md](./README.md) and [itr2/SKILL.md](./itr2/SKILL.md).
