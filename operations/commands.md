# Operations Commands

Run commands on the DGX Spark host from an SSH session.

## Service status
```bash
sudo systemctl status langgraph-agent --no-pager -l
```

## Recent service logs
```bash
sudo journalctl -u langgraph-agent -n 50 --no-pager
```

## Health
```bash
curl -sS -i http://127.0.0.1:8100/health
```

## Public model list
```bash
curl -sS http://127.0.0.1:8100/v1/models
```

## Compile and import check
```bash
cd /opt/ai/langgraph-agent
.venv/bin/python -m compileall -q app
.venv/bin/python -c "import app.main; print('Application import OK')"
```

Never print or paste the contents of `config/agent.env`; it contains secrets.
