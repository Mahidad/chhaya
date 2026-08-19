import psycopg
from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.concept_map import ConceptMapCreate, ConceptMapOut
from app.services import concept_map_service
from app.utils.exceptions import NotFoundError

router = APIRouter(prefix="/concept-maps", tags=["concept-maps"])


@router.post("", response_model=ConceptMapOut, status_code=status.HTTP_201_CREATED)
def create_concept_map(
    payload: ConceptMapCreate,
    db: psycopg.Connection = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Extracts nodes and edges and saves the map. Responds immediately --
    extraction is deterministic local processing (NLTK / ast / regex),
    not an AI call, so there's no status to poll.
    """
    try:
        return concept_map_service.create_concept_map(db, user_id=current_user.id, payload=payload)
    except ValueError as exc:
        # Unparseable code, unknown source_kind, or nothing extractable --
        # all things the student can fix, so 400 rather than 500.
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get("", response_model=list[ConceptMapOut])
def list_concept_maps(
    db: psycopg.Connection = Depends(get_db), current_user: User = Depends(get_current_user)
):
    return concept_map_service.list_concept_maps_for_user(db, user_id=current_user.id)


@router.get("/{concept_map_id}", response_model=ConceptMapOut)
def get_concept_map(
    concept_map_id: str,
    db: psycopg.Connection = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return concept_map_service.get_concept_map_for_user(
            db, user_id=current_user.id, concept_map_id=concept_map_id
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.delete("/{concept_map_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_concept_map(
    concept_map_id: str,
    db: psycopg.Connection = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        concept_map_service.delete_concept_map(
            db, user_id=current_user.id, concept_map_id=concept_map_id
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
