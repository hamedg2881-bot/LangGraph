# Roadmap

## Completed
- [x] Back up the relevant existing Agent application/config files before Registry work.
- [x] Create Registry SQL schema and tables in existing PostgreSQL database.
- [x] Implement async Registry database pool and repository.
- [x] Add separate secret admin key setting and Bearer authentication.
- [x] Implement admin model list, sync, approve/reject, update, enable/disable, and status endpoints.
- [x] Discover and register `qwen38-vl` as pending/disabled.
- [x] Compile/import checks passed.
- [x] Restart Agent and verify startup.
- [x] Verify health endpoint and unauthenticated admin rejection.
- [x] Verify authenticated admin list returns HTTP 200.

## In progress
- [ ] Inspect existing graph/model factory.
- [ ] Integrate request classification and Registry-based model selection.
- [ ] Preserve PostgreSQL checkpointer and conversation continuity.
- [ ] Expose only `Auto` from `/v1/models` after routing is tested.

## Later
- [ ] Define and assign verified capabilities to each model.
- [ ] Admin approval and enablement workflow, only after user decision.
- [ ] Test text, vision, coding, and tool-use routes with eligible workers.
- [ ] Improve runtime health checks beyond Dynamo model-list presence.
- [ ] Add operational/admin documentation and automated tests.
