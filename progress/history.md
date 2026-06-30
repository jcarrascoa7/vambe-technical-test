# Session History

Append-only log of completed sessions.

---

## Session: 2026-06-29 — Feature 0: bootstrap

**Status**: done
**Plan**:
1. Create backend skeleton: main.py, config.py, database.py, models.py, requirements.txt, tests/__init__.py
2. Create frontend skeleton: React+Vite app with package.json
3. Create docker-compose.yml (app + db services) and Dockerfile (multi-stage: Node build + Python)
4. Run ./init.sh to verify all checks pass

**Notes**: Building the foundation for all other features.
