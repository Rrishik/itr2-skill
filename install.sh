#!/usr/bin/env bash
# Install the itr-capital-gains skill into the chosen agent's skills directory.
# Usage: ./install.sh [copilot|claude|copilot-cli]   (default: copilot)
set -euo pipefail

target="${1:-copilot}"
case "$target" in
  copilot)     dest="$HOME/.agents/skills" ;;
  claude)      dest="$HOME/.claude/skills" ;;
  copilot-cli) dest="$HOME/.copilot/skills" ;;
  *) echo "Unknown target '$target'. Use: copilot | claude | copilot-cli" >&2; exit 1 ;;
esac

src="$(cd "$(dirname "$0")" && pwd)/itr-capital-gains"
mkdir -p "$dest"
cp -r "$src" "$dest/"
echo "Installed itr-capital-gains -> $dest/itr-capital-gains"
echo "Reload your agent to pick up the skill."
