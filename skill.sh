#!/usr/bin/env bash
set -euo pipefail

SKILL_NAME="shopify-theme-optimization"
SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"

usage() {
  cat <<'EOF'
Usage:
  ./skill.sh validate
  ./skill.sh install [--project|--global] [--agent AGENT|--agent all] [--target DIR]
  ./skill.sh package [OUT_DIR]

Examples:
  ./skill.sh validate
  ./skill.sh install --project --agent claude-code
  ./skill.sh install --global --agent codex
  ./skill.sh install --project --agent all
  ./skill.sh install --target .agents/skills

Known agent keys:
  agents, claude-code, codex, cursor, windsurf, opencode, goose, gemini-cli,
  github-copilot, amp, cline, continue, augment, roo, trae, kiro-cli,
  qwen-code, openhands, zencoder, all
EOF
}

python_bin() {
  if command -v python3 >/dev/null 2>&1; then
    echo python3
  elif command -v python >/dev/null 2>&1; then
    echo python
  else
    echo "python3 or python is required" >&2
    exit 1
  fi
}

project_skill_root() {
  case "$1" in
    agents|universal|amp|codex|codex-cli|cursor|github-copilot|cline|dexto|warp|gemini-cli|gemini|antigravity) echo ".agents/skills" ;;
    claude-code|claude) echo ".claude/skills" ;;
    windsurf) echo ".windsurf/skills" ;;
    opencode) echo ".opencode/skills" ;;
    goose) echo ".goose/skills" ;;
    continue) echo ".continue/skills" ;;
    augment) echo ".augment/skills" ;;
    roo) echo ".roo/skills" ;;
    trae|trae-cn) echo ".trae/skills" ;;
    kiro|kiro-cli) echo ".kiro/skills" ;;
    qwen|qwen-code) echo ".qwen/skills" ;;
    openhands) echo ".openhands/skills" ;;
    zencoder) echo ".zencoder/skills" ;;
    openclaw) echo "skills" ;;
    *) echo "" ;;
  esac
}

global_skill_root() {
  case "$1" in
    agents|universal|amp|cline|dexto|warp) echo "$HOME/.agents/skills" ;;
    codex|codex-cli) echo "$HOME/.codex/skills" ;;
    cursor) echo "$HOME/.cursor/skills" ;;
    github-copilot) echo "$HOME/.copilot/skills" ;;
    gemini|gemini-cli) echo "$HOME/.gemini/skills" ;;
    antigravity) echo "$HOME/.gemini/antigravity/skills" ;;
    claude-code|claude) echo "$HOME/.claude/skills" ;;
    windsurf) echo "$HOME/.codeium/windsurf/skills" ;;
    opencode) echo "$HOME/.config/opencode/skills" ;;
    goose) echo "$HOME/.config/goose/skills" ;;
    continue) echo "$HOME/.continue/skills" ;;
    augment) echo "$HOME/.augment/skills" ;;
    roo) echo "$HOME/.roo/skills" ;;
    trae) echo "$HOME/.trae/skills" ;;
    trae-cn) echo "$HOME/.trae-cn/skills" ;;
    kiro|kiro-cli) echo "$HOME/.kiro/skills" ;;
    qwen|qwen-code) echo "$HOME/.qwen/skills" ;;
    openhands) echo "$HOME/.openhands/skills" ;;
    zencoder) echo "$HOME/.zencoder/skills" ;;
    openclaw) echo "$HOME/.openclaw/skills" ;;
    *) echo "" ;;
  esac
}

validate() {
  test -f "$SCRIPT_DIR/SKILL.md" || { echo "missing SKILL.md" >&2; exit 1; }
  grep -q '^name: shopify-theme-optimization$' "$SCRIPT_DIR/SKILL.md" || { echo "SKILL.md name mismatch" >&2; exit 1; }
  grep -q '^description: ' "$SCRIPT_DIR/SKILL.md" || { echo "SKILL.md description missing" >&2; exit 1; }
  if grep -R "TODO" "$SCRIPT_DIR/SKILL.md" "$SCRIPT_DIR/references" >/dev/null 2>&1; then
    echo "found TODO markers" >&2
    exit 1
  fi
  py="$(python_bin)"
  "$py" -m py_compile "$SCRIPT_DIR/scripts/theme_audit.py" "$SCRIPT_DIR/scripts/image_inventory.py" "$SCRIPT_DIR/scripts/minify_assets.py"
  "$py" "$SCRIPT_DIR/scripts/theme_audit.py" --help >/dev/null
  "$py" "$SCRIPT_DIR/scripts/image_inventory.py" --help >/dev/null
  "$py" "$SCRIPT_DIR/scripts/minify_assets.py" --help >/dev/null
  echo "ok: $SKILL_NAME is valid"
}

copy_skill_to() {
  target_root="$1"
  mkdir -p "$target_root"
  dest="$target_root/$SKILL_NAME"
  src_real="$(cd "$SCRIPT_DIR" && pwd -P)"
  dest_parent_real="$(cd "$target_root" && pwd -P)"
  if [ "$src_real" = "$dest_parent_real/$SKILL_NAME" ]; then
    echo "already installed at $dest"
    return 0
  fi
  rm -rf "$dest"
  mkdir -p "$dest"
  py="$(python_bin)"
  "$py" - "$SCRIPT_DIR" "$dest" <<'PY'
import shutil
import sys
from pathlib import Path

src = Path(sys.argv[1]).resolve()
dest = Path(sys.argv[2]).resolve()
skip_names = {
    '.git', '__pycache__',
    '.agents', '.claude', '.codex', '.cursor', '.windsurf', '.opencode',
    '.goose', '.gemini', '.continue', '.augment', '.roo', '.trae', '.kiro',
    '.qwen', '.openhands', '.zencoder',
}

for path in src.rglob('*'):
    resolved = path.resolve()
    if resolved == dest or dest in resolved.parents:
        continue
    rel = path.relative_to(src)
    if any(part in skip_names for part in rel.parts):
        continue
    if path.suffix in {'.zip', '.bak', '.pyc', '.pyo'}:
        continue
    if path.is_file():
        target = dest / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)
PY
  echo "installed: $dest"
}

install_skill() {
  scope="project"
  agent="agents"
  target=""
  while [ "$#" -gt 0 ]; do
    case "$1" in
      --project) scope="project" ;;
      --global) scope="global" ;;
      --agent) shift; agent="${1:-}" ;;
      --target) shift; target="${1:-}" ;;
      --copy) ;;
      -h|--help) usage; exit 0 ;;
      *) echo "unknown install option: $1" >&2; usage; exit 1 ;;
    esac
    shift || true
  done

  validate >/dev/null

  if [ -n "$target" ]; then
    copy_skill_to "$target"
    return 0
  fi

  agents="agents claude-code codex cursor windsurf opencode goose gemini-cli github-copilot amp cline continue augment roo trae kiro-cli qwen-code openhands zencoder"
  if [ "$agent" != "all" ]; then
    agents="$agent"
  fi

  for a in $agents; do
    if [ "$scope" = "global" ]; then
      target_root="$(global_skill_root "$a")"
    else
      project_root="$(project_skill_root "$a")"
      target_root="./$project_root"
    fi
    if [ -z "$target_root" ] || [ "$target_root" = "./" ]; then
      echo "unknown agent: $a" >&2
      exit 1
    fi
    copy_skill_to "$target_root"
  done
}

package_skill() {
  out_dir="${1:-.}"
  validate >/dev/null
  mkdir -p "$out_dir"
  out_dir="$(cd "$out_dir" && pwd -P)"
  out_file="$out_dir/skill.zip"
  if command -v zip >/dev/null 2>&1; then
    (cd "$(dirname "$SCRIPT_DIR")" && zip -qr "$out_file" "$SKILL_NAME" \
      -x "$SKILL_NAME/.git/*" \
      -x "$SKILL_NAME/*.zip" \
      -x "$SKILL_NAME/**/__pycache__/*" \
      -x "$SKILL_NAME/**/*.bak")
  else
    py="$(python_bin)"
    "$py" - "$SCRIPT_DIR" "$out_file" "$SKILL_NAME" <<'PY'
import os
import sys
import zipfile
from pathlib import Path

src = Path(sys.argv[1]).resolve()
out_file = Path(sys.argv[2]).resolve()
skill_name = sys.argv[3]
exclude_names = {'.git', '__pycache__'}

with zipfile.ZipFile(out_file, 'w', zipfile.ZIP_DEFLATED) as archive:
    for path in src.rglob('*'):
        rel = path.relative_to(src)
        if any(part in exclude_names for part in rel.parts):
            continue
        if path.suffix in {'.zip', '.bak', '.pyc', '.pyo'}:
            continue
        if path.is_file():
            archive.write(path, Path(skill_name) / rel)
PY
  fi
  echo "packaged: $out_file"
}

cmd="${1:-}"
case "$cmd" in
  validate) shift; validate "$@" ;;
  install) shift; install_skill "$@" ;;
  package) shift; package_skill "$@" ;;
  -h|--help|help|"") usage ;;
  *) echo "unknown command: $cmd" >&2; usage; exit 1 ;;
esac
