---
name: course-delivery-conventions
description: How the django-lab training course is delivered — per-day guide files, student branch naming, and what students push
metadata:
  type: project
---

`django-lab` (github.com/kode-mafia008/django-lab) is a **teaching repo**, not a product. It serves a Django Framework Backend Development course run by the repo owner as trainer.

**Daily guides** live in `guides/README-day{N}.md` — one markdown file per teaching day, written in the same TYPE / EXPECT / CHECKPOINT / IF IT FAILS / WHY convention as the long-form `guides/django-practical-lab.md`. Day 1 (written 2026-08-26) covers GitHub auth via PAT and SSH key, cloning, branching, and scaffolding a Django project. Guides are **markdown, not PDF** — the trainer asked for markdown per day rather than a one-off rendered PDF.

Day 2 (2026-08-26) covers the project-vs-app distinction, `startapp blog`, `INSTALLED_APPS`, URLconf resolution, `Meta.db_table`, reading migrations with `sqlmigrate`, `createsuperuser`, and the admin. Every Django concept in the day-2 guide carries a **DOCS** link pinned to `docs.djangoproject.com/en/5.2/` (matching `requirements.txt`), plus a grouped link index in its Appendix B — keep that pinning when writing later days.

`.gitignore` ignores `guides/*.html` and `guides/*.sh` (the pandoc-generated HTML is 427KB and the build script is local tooling), but the markdown sources ARE tracked. See [[gitignore-catalog-migrations-trap]] for the one rule in that file that is easy to get wrong.

**Students branch as `{first_name}/day{N}`** — lowercase first name only, forward slash, no space or capitalisation. Each student clones `django-lab`, branches off `main`, and pushes to their own branch on the *same* repo (not a fork). Day 1 deliverable on each branch: a Django project scaffold plus a pinned `requirements.txt`, with `venv/` excluded.

**Why this matters when editing guides:** the repo root already contains a Django project (`config/` + `manage.py` + `catalog/`), so student `startproject` instructions must use a subfolder name (`day1_project`) rather than `startproject config .`, or they collide with the lab project.
