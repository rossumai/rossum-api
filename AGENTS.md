# AGENTS.md

## Commands
- **Test all:** `pytest tests/`
- **Test single:** `pytest tests/path/to/test_file.py::TestClass::test_name -x`
- **Lint:** `ruff check rossum_api/ tests/`
- **Format:** `ruff format rossum_api/ tests/`
- **Type check:** `ty check`

## API Reference
- Docs: https://rossum.app/api/docs/
- OpenAPI spec: https://rossum.app/api/docs/openapi/openapi-specs/openapi.external.json
- Use these when porting new endpoints. OpenAPI tags map to `Resource` enum values in `domain_logic/resources.py` (e.g. tag `Annotation` → `Resource.Annotation` → URL segment `"annotations"`). Operation IDs (e.g. `annotations_list`, `queues_create`) correspond to SDK methods like `list_annotations`, `create_new_queue`.
- Individual tag/operation pages: `https://rossum.app/api/docs/#tag/{Tag}` (e.g. `#tag/Queue`, `#tag/Annotation`) and `https://rossum.app/api/docs/#tag/{Tag}/operation/{operation_id}` (e.g. `#tag/Queue/operation/queues_list`, `#tag/Annotation/operation/annotations_create`).

## Architecture
Python SDK (`rossum_api/`) for the Rossum platform. Key layers:
- `clients/` — async (`external_async_client.py`) and sync (`external_sync_client.py`) public API clients, plus internal variants. Sync wraps async via `asyncio.run`.
- `models/` — dataclass-based domain models (Annotation, Document, Queue, Schema, Hook, etc.) deserialized with `dacite`.
- `domain_logic/` — URL builders and business logic helpers.
- `dtos.py`, `types.py`, `exceptions.py` — shared DTOs, type aliases, and `APIClientError`.

## Code Style
- Python 3.10+. Use `from __future__ import annotations` in every file (enforced by ruff isort).
- Formatter/linter: **ruff** (line-length 99, numpy-style docstrings, see `ruff.toml`).
- Type annotations required on all functions (checked by `ty check`).
- Imports: absolute only (`TID252`), stdlib → third-party → local, guarded `TYPE_CHECKING` imports.
- Tests use **pytest** + **pytest-asyncio** + **pytest-httpx**; test files mirror `rossum_api/` structure.
