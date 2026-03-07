from __future__ import annotations

import os
import sys
from pathlib import Path
from uuid import uuid4

from fileclassifier.models import ExecutionOptions, LogicOperator
from fileclassifier.services.excel_service import ExcelService
from fileclassifier.services.query_engine import apply_filters
from fileclassifier.services.workflow import execute_search
from fileclassifier.webapi.schemas import (
    DefaultPathsResponse,
    DirectoryListResponse,
    ExcelFileListResponse,
    ExcelMetadataRequest,
    ExcelMetadataResponse,
    ExcelUploadResponse,
    ExecutionRequest,
    ExecutionResponse,
    FilterPreviewRequest,
    FilterPreviewResponse,
    FramePayload,
    OpenFolderRequest,
    OpenFolderResponse,
    PickDirectoryRequest,
    PickDirectoryResponse,
    PickExcelFileRequest,
    PickExcelFileResponse,
    PickExcelSourceRequest,
    PickExcelSourceResponse,
    PreviewRequest,
    RecordMatchPayload,
)
from fileclassifier.webapi.utils.pathing import (
    EXCEL_FILE_SUFFIXES,
    list_excel_files,
    resolve_path,
    runtime_default_paths,
)
from fileclassifier.webapi.utils.serialization import build_conditions, frame_payload
from fileclassifier.webapi.utils.system_io import (
    list_directories,
    open_directory,
    pick_directory_dialog,
    pick_excel_file_dialog,
    pick_excel_source_dialog,
    system_roots,
)


def _resolve_frontend_dist() -> Path | None:
    env_dist = os.getenv("FILECLASSIFIER_FRONTEND_DIST", "").strip()
    candidates: list[Path] = []
    if env_dist:
        candidates.append(Path(env_dist).expanduser())

    meipass = getattr(sys, "_MEIPASS", "")
    if meipass:
        candidates.append(Path(meipass) / "frontend_dist")

    project_root = Path(__file__).resolve().parents[4]
    candidates.append(project_root / "fileclassifier-react-ui" / "dist")
    candidates.append(Path.cwd() / "fileclassifier-react-ui" / "dist")

    for candidate in candidates:
        index_file = candidate / "index.html"
        if candidate.is_dir() and index_file.exists():
            return candidate
    return None


def create_app():
    from fastapi import FastAPI, File, HTTPException, UploadFile
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import FileResponse
    from fastapi.staticfiles import StaticFiles

    app = FastAPI(title="FileClassifier API", version="1.0.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    frontend_dist = _resolve_frontend_dist()
    if frontend_dist:
        assets_dir = frontend_dist / "assets"
        if assets_dir.exists():
            app.mount("/assets", StaticFiles(directory=assets_dir), name="frontend-assets")

    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/api/system/default-paths", response_model=DefaultPathsResponse)
    def system_default_paths() -> DefaultPathsResponse:
        defaults = runtime_default_paths()
        return DefaultPathsResponse(
            mode=defaults.mode,
            base_dir=str(defaults.base_dir),
            excel_base_dir=str(defaults.excel_base_dir),
            input_dir=str(defaults.input_dir),
            output_dir=str(defaults.output_dir),
            logs_dir=str(defaults.logs_dir),
        )

    @app.get("/api/system/directories", response_model=DirectoryListResponse)
    def system_directories(path: str = "") -> DirectoryListResponse:
        defaults = runtime_default_paths()
        requested_path = resolve_path(path.strip()) if path.strip() else defaults.excel_base_dir
        try:
            current_path = requested_path.resolve()
        except OSError:
            current_path = requested_path

        if not current_path.exists():
            raise HTTPException(status_code=400, detail=f"Directory not found: {current_path}")
        if not current_path.is_dir():
            raise HTTPException(status_code=400, detail=f"Path is not a directory: {current_path}")

        try:
            roots = system_roots()
            directories = list_directories(current_path)
        except Exception as exc:  # pragma: no cover - surfaced as HTTP error
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        parent_path = current_path.parent if current_path.parent != current_path else None
        return DirectoryListResponse(
            current_path=str(current_path),
            parent_path=str(parent_path) if parent_path else None,
            roots=roots,
            directories=directories,
        )

    @app.post("/api/system/open-folder", response_model=OpenFolderResponse)
    def system_open_folder(payload: OpenFolderRequest) -> OpenFolderResponse:
        target = resolve_path(payload.path.strip())
        try:
            target = target.resolve()
        except OSError:
            pass

        if not target.exists():
            raise HTTPException(status_code=400, detail=f"Directory not found: {target}")
        if not target.is_dir():
            raise HTTPException(status_code=400, detail=f"Path is not a directory: {target}")

        try:
            open_directory(target)
        except Exception as exc:  # pragma: no cover - surfaced as HTTP error
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        return OpenFolderResponse(opened_path=str(target))

    @app.post("/api/system/pick-directory", response_model=PickDirectoryResponse)
    def system_pick_directory(payload: PickDirectoryRequest) -> PickDirectoryResponse:
        initial_path = payload.initial_path.strip()
        initial_dir = resolve_path(initial_path) if initial_path else Path.home()
        if not initial_dir.exists() or not initial_dir.is_dir():
            initial_dir = Path.home()

        try:
            selected = pick_directory_dialog(initial_dir)
        except Exception as exc:  # pragma: no cover - surfaced as HTTP error
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        if selected is None:
            return PickDirectoryResponse(selected_path=None, canceled=True)
        return PickDirectoryResponse(selected_path=str(selected), canceled=False)

    @app.post("/api/system/pick-excel-file", response_model=PickExcelFileResponse)
    def system_pick_excel_file(payload: PickExcelFileRequest) -> PickExcelFileResponse:
        initial_path = payload.initial_path.strip()
        initial_candidate = resolve_path(initial_path) if initial_path else Path.home()
        if initial_candidate.exists():
            initial_dir = initial_candidate if initial_candidate.is_dir() else initial_candidate.parent
        else:
            initial_dir = Path.home()

        try:
            selected = pick_excel_file_dialog(initial_dir)
        except Exception as exc:  # pragma: no cover - surfaced as HTTP error
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        if selected is None:
            return PickExcelFileResponse(selected_path=None, canceled=True)

        if selected.suffix.lower() not in EXCEL_FILE_SUFFIXES:
            raise HTTPException(status_code=400, detail="Only Excel files are supported.")
        return PickExcelFileResponse(selected_path=str(selected), canceled=False)

    @app.post("/api/system/pick-excel-source", response_model=PickExcelSourceResponse)
    def system_pick_excel_source(payload: PickExcelSourceRequest) -> PickExcelSourceResponse:
        initial_path = payload.initial_path.strip()
        initial_candidate = resolve_path(initial_path) if initial_path else Path.home()
        if initial_candidate.exists():
            initial_dir = initial_candidate if initial_candidate.is_dir() else initial_candidate.parent
        else:
            initial_dir = Path.home()

        try:
            selected_path, source_type = pick_excel_source_dialog(initial_dir)
        except Exception as exc:  # pragma: no cover - surfaced as HTTP error
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        if selected_path is None or source_type == "none":
            return PickExcelSourceResponse(selected_path=None, source_type="none", canceled=True)

        if source_type == "file" and selected_path.suffix.lower() not in EXCEL_FILE_SUFFIXES:
            raise HTTPException(status_code=400, detail="Only Excel files are supported.")
        if source_type == "directory" and not selected_path.is_dir():
            raise HTTPException(status_code=400, detail=f"Path is not a directory: {selected_path}")

        return PickExcelSourceResponse(
            selected_path=str(selected_path),
            source_type=source_type,
            canceled=False,
        )

    @app.get("/api/excel/files", response_model=ExcelFileListResponse)
    def excel_files(base_dir: str = "") -> ExcelFileListResponse:
        defaults = runtime_default_paths()
        normalized_base_dir = base_dir.strip()
        directory = resolve_path(normalized_base_dir) if normalized_base_dir else defaults.excel_base_dir
        try:
            files = list_excel_files(directory)
        except Exception as exc:  # pragma: no cover - surfaced as HTTP error
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return ExcelFileListResponse(base_dir=str(directory), files=files)

    @app.post("/api/excel/upload", response_model=ExcelUploadResponse)
    async def excel_upload(file: UploadFile = File(...)) -> ExcelUploadResponse:
        source_name = file.filename or ""
        suffix = Path(source_name).suffix.lower()
        if suffix not in EXCEL_FILE_SUFFIXES:
            raise HTTPException(status_code=400, detail="Only Excel files are supported.")

        upload_dir = runtime_default_paths().logs_dir / "uploaded_excels"
        upload_dir.mkdir(parents=True, exist_ok=True)
        target = upload_dir / f"{uuid4().hex}{suffix}"

        try:
            content = await file.read()
        finally:
            await file.close()

        if not content:
            raise HTTPException(status_code=400, detail="Uploaded file is empty.")

        try:
            target.write_bytes(content)
        except Exception as exc:  # pragma: no cover - surfaced as HTTP error
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        return ExcelUploadResponse(excel_path=str(target), filename=source_name or target.name)

    @app.post("/api/excel/metadata", response_model=ExcelMetadataResponse)
    def excel_metadata(payload: ExcelMetadataRequest) -> ExcelMetadataResponse:
        excel_path = resolve_path(payload.excel_path)
        try:
            sheet_names = ExcelService.list_sheets(excel_path)
        except Exception as exc:  # pragma: no cover - surfaced as HTTP error
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return ExcelMetadataResponse(sheet_names=sheet_names)

    @app.post("/api/excel/preview", response_model=FramePayload)
    def excel_preview(payload: PreviewRequest) -> FramePayload:
        excel_path = resolve_path(payload.excel_path)
        try:
            dataframe = ExcelService.read_sheet(excel_path, payload.sheet_name)
        except Exception as exc:  # pragma: no cover - surfaced as HTTP error
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return frame_payload(dataframe, payload.max_rows)

    @app.post("/api/query/filter-preview", response_model=FilterPreviewResponse)
    def filter_preview(payload: FilterPreviewRequest) -> FilterPreviewResponse:
        excel_path = resolve_path(payload.excel_path)
        try:
            dataframe = ExcelService.read_sheet(excel_path, payload.sheet_name)
            conditions = build_conditions(payload.conditions)
            filtered_dataframe, _ = apply_filters(
                dataframe=dataframe,
                conditions=conditions,
                logic=LogicOperator(payload.logic),
            )
        except Exception as exc:  # pragma: no cover - surfaced as HTTP error
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return FilterPreviewResponse(
            frame=frame_payload(filtered_dataframe, payload.max_rows),
            filtered_rows=len(filtered_dataframe),
        )

    @app.post("/api/workflow/execute", response_model=ExecutionResponse)
    def workflow_execute(payload: ExecutionRequest) -> ExecutionResponse:
        options = ExecutionOptions(
            excel_path=resolve_path(payload.excel_path),
            sheet_name=payload.sheet_name,
            input_dir=resolve_path(payload.input_dir),
            output_dir=resolve_path(payload.output_dir),
            recursive=payload.recursive,
        )
        try:
            report = execute_search(
                options=options,
                conditions=build_conditions(payload.conditions),
                logic=LogicOperator(payload.logic),
            )
        except Exception as exc:  # pragma: no cover - surfaced as HTTP error
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        serialized_matches: list[RecordMatchPayload] = []
        for item in report.record_matches:
            if item.conflict:
                status = "conflict"
            elif item.matched:
                status = "matched"
            else:
                status = "unmatched"
            serialized_matches.append(
                RecordMatchPayload(
                    record_number=item.record_number,
                    key_field=item.key_field,
                    key_value=item.key_value,
                    source_paths=[str(path) for path in item.source_paths],
                    copied_paths=[str(path) for path in item.copied_paths],
                    status=status,
                )
            )

        return ExecutionResponse(
            scanned_files=report.scanned_files,
            filtered_records=report.filtered_records,
            matched_records=report.matched_records,
            matched_files=report.matched_files,
            unmatched_records=report.unmatched_records,
            conflict_records=report.conflict_records,
            output_dir=str(report.output_dir),
            log_files=[str(path) for path in report.log_files],
            copied_files=[str(path) for path in report.copied_files],
            selected_columns=[
                {
                    "name": profile.name,
                    "score": profile.score,
                    "hit_ratio": profile.hit_ratio,
                    "uniqueness_ratio": profile.uniqueness_ratio,
                }
                for profile in report.selected_columns
            ],
            record_matches=serialized_matches,
        )

    if frontend_dist:
        index_file = frontend_dist / "index.html"

        @app.get("/", include_in_schema=False)
        def frontend_index():
            return FileResponse(index_file)

        @app.get("/{full_path:path}", include_in_schema=False)
        def frontend_fallback(full_path: str):
            if full_path.startswith("api/"):
                raise HTTPException(status_code=404, detail=f"Path not found: /{full_path}")

            candidate = frontend_dist / full_path
            if full_path and candidate.is_file():
                return FileResponse(candidate)
            return FileResponse(index_file)

    return app
