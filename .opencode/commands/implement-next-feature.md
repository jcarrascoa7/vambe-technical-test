---
description: Implement the next pending feature using leader → implementer → reviewer flow
agent: leader
---

Follow the leader protocol from @AGENTS.md:

1. Run `./init.sh`. If it fails, stop and report the error to the user.
2. Read @progress/current.md. If there is an active session or blocker, report it and stop.
3. Read @feature_list.json. Find the first feature with `status: "pending"` whose `depends_on` features are all `status: "done"`. If none exists, report that all features are done or blocked and stop.
4. Launch an **implementer** subagent with this instruction:

   > "Implement feature <id> — <name> from feature_list.json. Follow your full protocol: change status to in_progress, update progress/current.md, read the relevant docs, implement the acceptance criteria, write tests, run ./init.sh until green, and write progress/impl_<feature_name>.md. Your final response must be a single line: `done -> feature <id> implemented` or `blocked -> see progress/current.md`."

5. Wait for the implementer to finish.
6. If the implementer reports `blocked`, read `progress/current.md` to understand the blocker. Then launch the **implementer** again with this instruction:

   > "Mark feature <id> as `blocked` in feature_list.json. Then move the summary from progress/current.md to the end of progress/history.md. Empty progress/current.md leaving only the template."

   Report the blocker to the user and stop.
7. If the implementer reports `done`, launch a **reviewer** subagent with this instruction:

   > "Review feature <id> — <name>. Read docs/architecture.md, docs/conventions.md, docs/verification.md, CHECKPOINTS.md. Check all files modified by the implementer. Run ./init.sh. Write your verdict to progress/review_<id>.md. Your final response must be a single line: `APPROVED -> see progress/review_<id>.md` or `CHANGES_REQUESTED -> see progress/review_<id>.md`."

8. Wait for the reviewer to finish.
9. If the reviewer reports `CHANGES_REQUESTED`, read `progress/review_<id>.md`, report the required changes to the user, and stop. Do NOT attempt fixes without user approval.
10. If the reviewer reports `APPROVED`, launch the **implementer** again for session close:

    > "Close session for feature <id>. Follow step 9 of your protocol: mark feature as done in feature_list.json, move summary from progress/current.md to progress/history.md, empty progress/current.md to template only, and run ./init.sh one final time. Your final response must be: `session closed -> feature <id> done`."

11. Report to the user: feature <id> is done, PR pending.
