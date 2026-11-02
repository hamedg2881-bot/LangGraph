# Troubleshooting

## Agent startup fails
1. Check `sudo systemctl status langgraph-agent --no-pager -l`.
2. Read recent logs with `sudo journalctl -u langgraph-agent -n 100 --no-pager`.
3. Check Python compilation/import before attempting another restart.
4. Preserve existing database/checkpointer data.

## Admin API returns 503
The application reports admin API unconfigured when `ADMIN_API_KEY` is absent from the loaded settings. Verify presence without printing its value.

## Admin API returns 401
Verify the Bearer header and the host-side key source. Never paste the key into chat or logs.

## Registry startup/database issue
Check PostgreSQL connectivity and Registry schema initialization. Registry tables are prefixed `model_registry_`; do not alter or delete checkpointer tables.

## Model is not selectable
Check approval, enablement, required capability, and live Dynamo availability independently. A discovered model remains pending/disabled until an administrator explicitly changes it.
