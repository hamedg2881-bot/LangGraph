# LangGraph Agent on NVIDIA DGX Spark

Private project notebook and change archive for the LangGraph Agent deployed on NVIDIA DGX Spark.

## Purpose

This repository records the agreed architecture, implementation decisions, deployment configuration templates, database schema, operational procedures, current status, and sanitized snapshots of project files.

## Safety

- Never commit `config/agent.env`, API keys, passwords, tokens, private credentials, runtime databases, model weights, or user data.
- Store sanitized templates only.
- Do not overwrite production configuration from this repository without an explicit review and approval.

## Documentation

- [Project context](PROJECT_CONTEXT.md)
- [Architecture](architecture/overview.md)
- [Unified model management architecture](architecture/model-management.md)
- [Architecture decisions](architecture/decisions.md)
- [Current status](progress/current-status.md)
- [Roadmap](progress/roadmap.md)
- [Change log](CHANGELOG.md)
- [Tracked file inventory](source/FILE_INVENTORY.md)
- [Database schema](database/schema.sql)
- [Deployment notes](deployment/services.md)
- [Existing Control Center](deployment/control-center.md)
- [Environment template](deployment/agent.env.example)
- [Operations](operations/commands.md)

## Update policy

After each project change, update the relevant sanitized source/configuration snapshot and the project context, current status, and change log in the same work session.


## Agent Model Manager source

- [Agent source tree](source/app/)
- [Model Manager implementation](source/app/model_manager.py)
- [Agent Registry schema and queue/lease tables](source/app/registry/schema.sql)
- [Current implementation and deployment gates](progress/current-status.md)
