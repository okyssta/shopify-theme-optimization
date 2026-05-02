# Tooling and Agent Installation Notes

## Skill format

This skill is a portable directory with `SKILL.md` at the root. That is the common Agent Skills pattern used by ChatGPT/OpenAI skills, Codex skills, Claude Code skills, and skills.sh-compatible skill directories.

## Common install locations

Project-scoped:
- `.agents/skills/shopify-theme-optimization/`
- `.claude/skills/shopify-theme-optimization/`
- `.codex/skills/shopify-theme-optimization/`

User/global:
- `~/.agents/skills/shopify-theme-optimization/`
- `~/.claude/skills/shopify-theme-optimization/`
- `~/.codex/skills/shopify-theme-optimization/`

For tools managed by the skills.sh CLI, publish or keep this folder in a Git repository and install it with the CLI from the repository or local path.

## Included helper

`skill.sh` is a lightweight local helper for this package:

```bash
./skill.sh validate
./skill.sh install --project --agent claude-code
./skill.sh install --global --agent codex
./skill.sh install --project --agent all --copy
```

The helper intentionally uses copy mode by default for portability. If your agent ecosystem uses symlinks or the official skills.sh CLI, prefer that workflow.

## Shopify tooling to use when available

- Shopify CLI and Theme Check for Liquid/theme linting.
- Lighthouse or PageSpeed Insights for lab metrics.
- Chrome Performance panel or WebPageTest for deeper JavaScript/INP analysis.
- Git diff and visual regression tools for conversion-safety checks.

Never claim a Lighthouse/Core Web Vitals score improved unless a before/after measurement was actually run.
