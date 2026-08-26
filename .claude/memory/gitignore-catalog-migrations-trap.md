---
name: gitignore-catalog-migrations-trap
description: catalog/ is untracked on purpose (trainer-owned, local-only) — and why gitignore alone never achieved that
metadata:
  type: project
---

**Current state (2026-08-26):** `catalog/` is **untracked**. It exists on the trainer's disk but is not in the repo. `config/settings.py` and `config/urls.py` therefore must NOT reference it — `'catalog'` was removed from `INSTALLED_APPS` and `path("catalog/", include("catalog.urls"))` from the root URLconf, or a fresh clone dies with `ModuleNotFoundError: No module named 'catalog'` before Django starts.

**The lesson that got us there:** adding `catalog/` to `.gitignore` did nothing on its own, because **gitignore is only consulted for untracked files**. All 18 catalog files had been tracked since the initial commit `4c4374e`, so they kept showing up in `git status` and on GitHub. Untracking required `git rm -r --cached catalog`.

The asymmetry is the dangerous part, and it bit us before the removal: an ignore rule over a partly-tracked directory leaves existing files visible while silently swallowing *new* ones. `Author.Meta.db_table = "authors"` was staged normally while its `catalog/migrations/0002_alter_author_table.py` was invisible to `git status` — which would have shipped a model whose declared table had no migration to rename it.

**How to apply:**
- If `git status` fails to show a file you expect, run `git check-ignore -v <path>`. Exit 1 means no rule matched — the file is tracked, and gitignore is irrelevant to it.
- Never reach for `git add -f` to work around this; it hides the rule bug and the next new file vanishes too.
- A negation like `!catalog/migrations/` cannot rescue a bare `catalog/` rule — git never descends into an excluded *directory*. Excluding contents (`catalog/*`) is the only form a negation can follow.
- Anything re-added under `catalog/` from now on needs `git add -f`, by design.

See [[course-delivery-conventions]] — note the day-2 guide still teaches against `catalog`, which students can no longer clone.
