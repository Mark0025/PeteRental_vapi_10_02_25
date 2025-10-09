# Deprecated Files

This directory contains files that are no longer used in the current architecture.

## Categories

### Fix/Debug Scripts (12 files)
- `fix_vapi_*.py` - One-off debugging scripts from development
- `check_*.py` - Configuration verification scripts
- `verify_*.py` - Status checking scripts
- `update_*.py` - Manual configuration scripts
- `attach_*.py` - Old VAPI SDK approach (deprecated)
- `test_webhook.py`, `test_production_webhook.py` - Basic tests (consolidated)

### Unused Architecture (src/)
- `api/` - Alternative VAPI router (different project)
- `models/` - Pydantic models for unused router
- `services/` - Provider services (unused)
- `ai/` - Model manager (different project)
- `config/` - Settings (different project)
- `utils/` - Logger wrapper (using loguru directly)

## Why Deprecated?

These files were from:
1. Debugging sessions during initial setup
2. Different project architecture that was mixed in
3. Outdated approaches to VAPI integration

## Can I Delete?

Yes, after verifying production works with current clean architecture.
Keep for 30 days as backup, then delete.

## Current Architecture

See `PROJECT_MASTER.md` for the clean, working architecture.
