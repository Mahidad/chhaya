"""
Orchestration for Code Studio's Visualizer: create a code_visualizations
row, call the Gemini-backed trace generator (code_visualization_service.py),
update status, handle failure. Same skeleton as code_converter_service.py --
create-then-process-then-update-status.
"""

import psycopg

from app.models.code_visualization import VisualizationStatus
from app.repositories.code_visualization_repository import code_visualization_repository
from app.schemas.code_visualization import CodeVisualizationCreate, CodeVisualizationUpdate
from app.services import code_visualization_service
from app.utils.exceptions import NotFoundError


def create_and_visualize(db: psycopg.Connection, *, user_id: str, payload: CodeVisualizationCreate):
    # Re-tracing the same code refreshes the existing row instead of adding
    # a duplicate beside it -- see CodeConversionRepository.find_identical
    # for the full reasoning.
    existing = code_visualization_repository.find_identical(
        db, user_id=user_id, language=payload.language, source_code=payload.source_code
    )
    if existing:
        changes = {"status": VisualizationStatus.PENDING, "error_message": None}
        if payload.folder_id:
            changes["folder_id"] = payload.folder_id
        visualization = code_visualization_repository.update(db, db_obj=existing, obj_in=changes)
    else:
        visualization = code_visualization_repository.create(
            db,
            obj_in={
                "user_id": user_id,
                "language": payload.language,
                "source_code": payload.source_code,
                "folder_id": payload.folder_id,
                "status": VisualizationStatus.PENDING,
            },
        )

    try:
        visualization = code_visualization_repository.update(
            db, db_obj=visualization, obj_in={"status": VisualizationStatus.GENERATING}
        )

        result = code_visualization_service.generate_trace(
            source_code=payload.source_code, language=payload.language
        )

        visualization = code_visualization_repository.update(
            db,
            db_obj=visualization,
            obj_in={
                "status": VisualizationStatus.READY,
                "trace": result.get("steps") or [],
                "explanation": result.get("explanation"),
            },
        )
    except Exception as exc:  # noqa: BLE001
        visualization = code_visualization_repository.update(
            db, db_obj=visualization, obj_in={"status": VisualizationStatus.FAILED, "error_message": str(exc)}
        )

    return visualization


def list_visualizations_for_user(db: psycopg.Connection, *, user_id: str):
    return code_visualization_repository.list_for_user(db, user_id=user_id)


def get_visualization_for_user(db: psycopg.Connection, *, user_id: str, visualization_id: str):
    visualization = code_visualization_repository.get_for_user(
        db, visualization_id=visualization_id, user_id=user_id
    )
    if not visualization:
        raise NotFoundError("Visualization not found.")
    return visualization


def update_visualization(db: psycopg.Connection, *, user_id: str, visualization_id: str, payload: CodeVisualizationUpdate):
    visualization = get_visualization_for_user(db, user_id=user_id, visualization_id=visualization_id)
    changes = payload.model_dump(exclude_unset=True)
    return code_visualization_repository.update(db, db_obj=visualization, obj_in=changes)


def delete_visualization(db: psycopg.Connection, *, user_id: str, visualization_id: str) -> None:
    visualization = get_visualization_for_user(db, user_id=user_id, visualization_id=visualization_id)
    code_visualization_repository.delete(db, id=visualization.id)
