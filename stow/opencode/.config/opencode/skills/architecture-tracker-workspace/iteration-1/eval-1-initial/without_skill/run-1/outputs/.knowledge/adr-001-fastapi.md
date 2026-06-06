# ADR-001: Use FastAPI as the Web Framework

## Status

Accepted

## Context

We need a web framework for building the project's API layer. The key requirements are:

- **Async support**: The application will handle concurrent I/O-bound operations (database queries, external API calls) and must not block threads.
- **Type safety**: The codebase should leverage Python type hints to reduce runtime errors and improve developer experience via editor autocompletion and static analysis.
- **Modern standards**: The framework should follow OpenAPI/Swagger specifications for auto-generated documentation.

## Decision

We will use **FastAPI** as the web framework.

## Rationale

| Criteria | FastAPI | Flask | Django | Litestar |
|---|---|---|---|---|
| Async native | Yes | Limited (via extensions) | Partial (3.1+) | Yes |
| Type safety | First-class (Pydantic) | No | No | Yes (attrs/msgspec) |
| OpenAPI docs | Auto-generated | Extensions needed | Extensions needed | Auto-generated |
| Ecosystem maturity | High | Very High | Very High | Growing |
| Performance | Excellent | Moderate | Moderate | Excellent |

FastAPI is the best fit because:

1. **Native async/await** — Built on Starlette and designed for asyncio from the ground up. No need for worker threads or extension libraries.
2. **Pydantic integration** — Request/response validation and serialization are driven by Python type annotations, providing compile-time-like safety in an interpreted language.
3. **Auto-generated OpenAPI docs** — Swagger UI and ReDoc are available out of the box at `/docs` and `/redoc`.
4. **Strong ecosystem** — Widely adopted, well-documented, and supported by a large community.

## Consequences

- Team members must be familiar with `async`/`await` patterns and `asyncio`.
- Database drivers and libraries must support async (e.g., `asyncpg`, `SQLAlchemy` async mode, `httpx` for HTTP clients).
- The project will adopt Pydantic models for all request/response schemas.
