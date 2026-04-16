# Fix Celery Model Bootstrap For Document Processing

## Summary
The failure is not in document confirmation itself; it starts earlier in the async pipeline. `process_document` crashes inside the Celery worker on the first `db.query(Document)` because SQLAlchemy tries to resolve `Document.owner = relationship("User")`, but the worker boot path has not imported `app.models.user`. The FastAPI process avoids this because auth dependencies import `User`, so the mapper registry is complete there.

## Implementation Changes
- Add a single, explicit ORM bootstrap on the worker startup path so Celery always imports the full model set before any task touches `Document`, `ChatSession`, or other string-based relationships.
- Use the existing `app.db.base` module as the canonical import point rather than importing `User` ad hoc inside tasks.
- Wire that bootstrap into the Celery entry path with one of these equivalent patterns, preferring the simplest shared one:
  1. Import `app.db.base` in `app/worker.py` before task imports
  2. Or import `app.db.base` in `app/tasks/__init__.py` so autodiscovery also guarantees mapper registration
- Keep task behavior unchanged; this is a startup/bootstrap fix, not a document-processing logic change.
- Optionally add a short code comment near the bootstrap import explaining that Celery must preload all ORM models for SQLAlchemy relationship resolution.

## Public Interfaces / Behavior
- No API contract changes
- No schema or migration changes
- Expected behavioral change: document upload should continue into async parsing/fact extraction in Celery instead of leaving the UI stuck with `Document facts are not ready for review`

## Test Plan
- Add a regression test that exercises the worker import path, not just direct task imports:
  - import `app.worker`
  - then create/query a `Document` or run `process_document.run(...)`
  - assert no `InvalidRequestError` about unresolved `User`
- Keep the existing task registration tests, and extend them so they verify worker startup also initializes model mappings safely.
- Re-run the document async tests around `process_document` and `extract_document_facts` to confirm the bootstrap change does not affect queueing or status transitions.
- Manual verification after implementation:
  1. Start API on `127.0.0.1:8000`
  2. Start Celery worker on `document-high-priority`
  3. Upload a PDF
  4. Confirm the worker logs progress past `db.query(Document)` into parsing/fact extraction
  5. Re-open the document and confirm the `409 Document facts are not ready for review` disappears once extraction completes

## Assumptions
- The intended architecture is that `app.db.base` remains the one place that imports all ORM models for registry side effects.
- The `409` seen in the UI is secondary fallout from the failed background task, not a separate frontend bug.
- No additional hidden mapper failures exist beyond `User`; importing the full model set should also protect other string-based relationships like `ChatSession.owner`.
