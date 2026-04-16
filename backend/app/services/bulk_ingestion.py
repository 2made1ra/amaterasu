import argparse
import math
import uuid
from dataclasses import dataclass
from pathlib import Path

import httpx

from app.core.config import settings


@dataclass(slots=True)
class BulkUploadRequest:
    file_path: Path
    batch_id: str
    trusted_import: bool


def discover_input_files(folder: str | Path) -> list[Path]:
    root = Path(folder)
    if not root.exists():
        raise FileNotFoundError(f"Input folder does not exist: {root}")
    return sorted(path for path in root.iterdir() if path.is_file() and path.suffix.lower() == ".pdf")


def split_into_batches(file_paths: list[Path], batch_size: int = settings.BULK_IMPORT_BATCH_SIZE) -> list[list[Path]]:
    if batch_size <= 0:
        raise ValueError("batch_size must be positive")
    return [file_paths[index:index + batch_size] for index in range(0, len(file_paths), batch_size)]


def build_batch_id(batch_prefix: str, batch_index: int, total_batches: int) -> str:
    return f"{batch_prefix}-{batch_index:03d}-of-{total_batches:03d}"


def build_upload_plan(
    file_paths: list[Path],
    *,
    batch_size: int = settings.BULK_IMPORT_BATCH_SIZE,
    batch_prefix: str | None = None,
    trusted_import: bool = False,
) -> list[BulkUploadRequest]:
    batches = split_into_batches(file_paths, batch_size=batch_size)
    if not batches:
        return []

    prefix = batch_prefix or f"bulk-{uuid.uuid4().hex[:12]}"
    total_batches = len(batches)
    upload_requests: list[BulkUploadRequest] = []
    for batch_number, batch_paths in enumerate(batches, start=1):
        batch_id = build_batch_id(prefix, batch_number, total_batches)
        upload_requests.extend(
            BulkUploadRequest(file_path=path, batch_id=batch_id, trusted_import=trusted_import)
            for path in batch_paths
        )
    return upload_requests


class HttpDocumentUploader:
    def __init__(self, *, api_base_url: str, token: str):
        self._client = httpx.Client(
            base_url=api_base_url.rstrip("/"),
            headers={"Authorization": f"Bearer {token}"},
            timeout=30.0,
        )

    def upload(self, request: BulkUploadRequest) -> dict:
        with request.file_path.open("rb") as file_handle:
            response = self._client.post(
                f"{settings.API_V1_PREFIX}/documents/upload",
                files={"file": (request.file_path.name, file_handle, "application/pdf")},
                data={
                    "batch_id": request.batch_id,
                    "ingestion_source": "BULK_IMPORT",
                    "queue_priority": "LOW",
                    "trusted_import": str(request.trusted_import).lower(),
                },
            )
        response.raise_for_status()
        return response.json()

    def close(self) -> None:
        self._client.close()


def run_bulk_import(
    folder: str | Path,
    *,
    uploader,
    batch_size: int = settings.BULK_IMPORT_BATCH_SIZE,
    batch_prefix: str | None = None,
    trusted_import: bool = False,
) -> list[dict]:
    file_paths = discover_input_files(folder)
    upload_plan = build_upload_plan(
        file_paths,
        batch_size=batch_size,
        batch_prefix=batch_prefix,
        trusted_import=trusted_import,
    )
    results = []
    for request in upload_plan:
        response = uploader.upload(request)
        results.append(
            {
                "document_id": response.get("document_id"),
                "file_path": str(request.file_path),
                "batch_id": request.batch_id,
            }
        )
    return results


def _build_cli_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Bulk import contracts through the existing upload API.")
    parser.add_argument("folder", help="Folder containing PDF files")
    parser.add_argument("--api-base-url", default="http://localhost:8000", help="API base URL without the /api/v1 suffix")
    parser.add_argument("--token", required=True, help="Bearer token for the upload user")
    parser.add_argument("--batch-size", type=int, default=settings.BULK_IMPORT_BATCH_SIZE, help="Maximum documents per batch")
    parser.add_argument("--batch-prefix", default=None, help="Optional human-readable prefix for generated batch ids")
    parser.add_argument("--trusted-import", action="store_true", help="Mark uploaded documents as trusted bulk imports")
    return parser


def main() -> int:
    parser = _build_cli_parser()
    args = parser.parse_args()
    uploader = HttpDocumentUploader(api_base_url=args.api_base_url, token=args.token)
    try:
        results = run_bulk_import(
            args.folder,
            uploader=uploader,
            batch_size=args.batch_size,
            batch_prefix=args.batch_prefix,
            trusted_import=args.trusted_import,
        )
    finally:
        uploader.close()

    total_batches = math.ceil(len(results) / args.batch_size) if results else 0
    print(f"Uploaded {len(results)} documents across {total_batches} batch(es)")
    for result in results:
        print(f"{result['batch_id']} :: {result['document_id']} :: {result['file_path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
