"""
A generic CRUD base class.

WHY THIS EXISTS:
This is the piece that directly answers "we need reusable CRUD patterns"
for the no-AI live exam. Every table in Chhaya (sources, profiles, quizzes,
flashcards, bookmarks...) needs the same five operations: get one, get
many, create, update, delete. Writing that from scratch for all ~15 tables
across 4 people's modules is repetitive and easy to get subtly wrong.

Instead, each specific repository (e.g. ReferenceSourceRepository) just
inherits from `BaseRepository` and gets get/get_multi/create/update/delete
for free, then adds only the queries that are genuinely specific to that
table (like "get all sources for this user").

This is the *only* layer allowed to import `Session` and write `db.query(...)`.
Services never touch the DB directly -- they call a repository.
"""

from typing import Generic, TypeVar, Type, Any

from sqlalchemy.orm import Session

ModelType = TypeVar("ModelType")


class BaseRepository(Generic[ModelType]):
    def __init__(self, model: Type[ModelType]):
        self.model = model

    def get(self, db: Session, id: str) -> ModelType | None:
        return db.query(self.model).filter(self.model.id == id).first()

    def get_multi(
        self, db: Session, *, skip: int = 0, limit: int = 100, **filters: Any
    ) -> list[ModelType]:
        query = db.query(self.model)
        for field, value in filters.items():
            query = query.filter(getattr(self.model, field) == value)
        return query.offset(skip).limit(limit).all()

    def create(self, db: Session, *, obj_in: dict) -> ModelType:
        db_obj = self.model(**obj_in)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(self, db: Session, *, db_obj: ModelType, obj_in: dict) -> ModelType:
        for field, value in obj_in.items():
            setattr(db_obj, field, value)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def delete(self, db: Session, *, id: str) -> None:
        obj = self.get(db, id)
        if obj:
            db.delete(obj)
            db.commit()
