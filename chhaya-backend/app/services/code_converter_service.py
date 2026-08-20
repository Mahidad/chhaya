"""
Orchestration for the HLL Code Converter feature: create a code_conversions
row, call the Gemini-backed generation layer (code_conversion_service.py --
note the similar name, different job: that file is the pure "call Gemini,
get JSON back" layer, mirroring how guide_generation_service.py relates to
study_guide_service.py), apply crude style post-processing if requested,
update status, handle failure. Same create-then-process-then-update-status
skeleton as every other AI-backed feature in this app.

STYLE APPLICATION, TWO LAYERS: if a code_style_profile_id is given, its
attributes go into the Gemini prompt itself (so naming convention gets
applied with real understanding of the code, not blind find/replace --
see the reasoning in code_style_analyzer.py's apply_style() docstring for
why renaming isn't done as a crude pass), AND the crude, whitespace-only
apply_style() pass runs on the result afterward as a safety net for
indentation/brace placement specifically, which CAN be enforced
mechanically without risk of changing what the code does.
"""

import psycopg

from app.models.code_conversion import ConversionMode, ConversionStatus
from app.repositories.code_conversion_repository import code_conversion_repository
from app.repositories.code_style_profile_repository import code_style_profile_repository
from app.schemas.code_conversion import CodeConversionSolveCreate, CodeConversionTranslateCreate, CodeConversionUpdate
from app.services import code_conversion_service
from app.utils.code_style_analyzer import apply_style
from app.utils.exceptions import NotFoundError


def _style_dict_for(db: psycopg.Connection, *, user_id: str, code_style_profile_id: str | None) -> dict | None:
    if not code_style_profile_id:
        return None
    profile = code_style_profile_repository.get(db, code_style_profile_id)
    if not profile or str(profile.user_id) != str(user_id):
        raise NotFoundError("Coding style profile not found.")
    return {
        "indent_style": profile.indent_style,
        "indent_size": profile.indent_size,
        "naming_convention": profile.naming_convention,
        "brace_style": profile.brace_style,
        "loop_style": profile.loop_style,
        "branching_style": profile.branching_style,
        "max_nesting_depth": profile.max_nesting_depth,
    }


def _reuse_or_create(db: psycopg.Connection, *, user_id: str, fields: dict, folder_id: str | None):
    """Return the row this generation should write into.

    RE-RUNNING OVERWRITES INSTEAD OF PILING UP: pressing Translate twice on
    the same source used to leave two identical rows in the same folder,
    which is what the user sees as "the same file added again". Identical
    inputs can only produce the same kind of output, so a re-run refreshes
    the existing row rather than creating a sibling.

    Changing anything that affects the output -- the code, the target
    language -- is NOT identical, so those still create separate rows. The
    style profile is excluded from that identity on purpose; see
    CodeConversionRepository.find_identical.

    An explicit folder_id on the request wins; otherwise the existing row
    keeps whatever folder the user already filed it into.
    """
    existing = code_conversion_repository.find_identical(
        db,
        user_id=user_id,
        mode=fields["mode"],
        target_language=fields["target_language"],
        source_code=fields.get("source_code"),
        problem_statement=fields.get("problem_statement"),
    )
    if existing:
        # Write this request's inputs onto the existing row -- the style
        # profile in particular, since it is not part of the identity and
        # may well be what changed. folder_id and title are left alone so a
        # re-run never un-files or renames something the user organised.
        changes = {**fields, "status": ConversionStatus.PENDING, "error_message": None}
        if folder_id:
            changes["folder_id"] = folder_id
        return code_conversion_repository.update(db, db_obj=existing, obj_in=changes)

    return code_conversion_repository.create(
        db, obj_in={**fields, "user_id": user_id, "folder_id": folder_id, "status": ConversionStatus.PENDING}
    )


def create_and_translate(db: psycopg.Connection, *, user_id: str, payload: CodeConversionTranslateCreate):
    style = _style_dict_for(db, user_id=user_id, code_style_profile_id=payload.code_style_profile_id)

    conversion = _reuse_or_create(
        db,
        user_id=user_id,
        fields={
            "mode": ConversionMode.TRANSLATE,
            "source_language": payload.source_language,
            "target_language": payload.target_language,
            "source_code": payload.source_code,
            "code_style_profile_id": payload.code_style_profile_id,
        },
        folder_id=payload.folder_id,
    )

    try:
        conversion = code_conversion_repository.update(
            db, db_obj=conversion, obj_in={"status": ConversionStatus.GENERATING}
        )

        result = code_conversion_service.translate_code(
            source_code=payload.source_code,
            source_language=payload.source_language,
            target_language=payload.target_language,
            style=style,
        )

        output_code = result["output_code"]
        if style:
            output_code = apply_style(output_code, style)

        conversion = code_conversion_repository.update(
            db,
            db_obj=conversion,
            obj_in={
                "status": ConversionStatus.READY,
                "source_language": result.get("detected_source_language") or payload.source_language,
                "output_code": output_code,
                "mapping": result.get("mapping") or [],
                "explanation": result.get("explanation"),
            },
        )
    except Exception as exc:  # noqa: BLE001
        conversion = code_conversion_repository.update(
            db, db_obj=conversion, obj_in={"status": ConversionStatus.FAILED, "error_message": str(exc)}
        )

    return conversion


def create_and_solve(db: psycopg.Connection, *, user_id: str, payload: CodeConversionSolveCreate):
    style = _style_dict_for(db, user_id=user_id, code_style_profile_id=payload.code_style_profile_id)

    conversion = _reuse_or_create(
        db,
        user_id=user_id,
        fields={
            "mode": ConversionMode.SOLVE,
            "target_language": payload.target_language,
            "problem_statement": payload.problem_statement,
            "code_style_profile_id": payload.code_style_profile_id,
        },
        folder_id=payload.folder_id,
    )

    try:
        conversion = code_conversion_repository.update(
            db, db_obj=conversion, obj_in={"status": ConversionStatus.GENERATING}
        )

        result = code_conversion_service.solve_problem(
            problem_statement=payload.problem_statement,
            target_language=payload.target_language,
            style=style,
        )

        output_code = result["output_code"]
        if style:
            output_code = apply_style(output_code, style)

        conversion = code_conversion_repository.update(
            db,
            db_obj=conversion,
            obj_in={
                "status": ConversionStatus.READY,
                "output_code": output_code,
                "explanation": result.get("explanation"),
            },
        )
    except Exception as exc:  # noqa: BLE001
        conversion = code_conversion_repository.update(
            db, db_obj=conversion, obj_in={"status": ConversionStatus.FAILED, "error_message": str(exc)}
        )

    return conversion


def list_conversions_for_user(db: psycopg.Connection, *, user_id: str):
    return code_conversion_repository.list_for_user(db, user_id=user_id)


def get_conversion_for_user(db: psycopg.Connection, *, user_id: str, conversion_id: str):
    conversion = code_conversion_repository.get_for_user(db, conversion_id=conversion_id, user_id=user_id)
    if not conversion:
        raise NotFoundError("Conversion not found.")
    return conversion


def update_conversion(db: psycopg.Connection, *, user_id: str, conversion_id: str, payload: CodeConversionUpdate):
    """Rename, favorite, or move to a folder -- the storage/organization
    system, not a re-run. Re-running with different inputs is always a
    new POST, same as everything else in this app that generates content."""
    conversion = get_conversion_for_user(db, user_id=user_id, conversion_id=conversion_id)
    changes = payload.model_dump(exclude_unset=True)
    return code_conversion_repository.update(db, db_obj=conversion, obj_in=changes)


def delete_conversion(db: psycopg.Connection, *, user_id: str, conversion_id: str) -> None:
    conversion = get_conversion_for_user(db, user_id=user_id, conversion_id=conversion_id)
    code_conversion_repository.delete(db, id=conversion.id)
