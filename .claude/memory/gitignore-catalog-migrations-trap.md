---
name: gitignore-catalog-migrations-trap
description: Why .gitignore uses catalog/* rather than catalog/, and why the migrations negation must never be removed
metadata:
  type: project
---

`.gitignore` deliberately reads `catalog/*` (contents) rather than `catalog/` (directory), followed by `!catalog/migrations/`.

**Why the star matters:** git never descends into an excluded *directory*, so a bare `catalog/` makes any later negation impossible — `!catalog/migrations/` silently does nothing. Excluding the contents instead leaves the directory walkable so the negation can take effect.

**Why the negation matters:** `catalog/` has ~17 already-tracked files, and gitignore never applies to tracked files — so `catalog/models.py` keeps showing as modified and gets committed normally. Only *new* files are swallowed. That asymmetry is what makes this dangerous: on 2026-08-26 the `Author.Meta.db_table = "authors"` change was staged while its `catalog/migrations/0002_alter_author_table.py` was invisible to `git status`. Committing that pair would have shipped a model whose declared table has no migration to rename it — every clone's `migrate` does nothing and the schema silently diverges from the model.

**How to apply:** if `git status` ever fails to show a new `catalog/` file you expect, run `git check-ignore -v <path>` before reaching for `git add -f`. Force-adding hides the rule bug and the *next* migration disappears too. Fix the rule instead. See [[course-delivery-conventions]].
