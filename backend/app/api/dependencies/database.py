from collections.abc import Generator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.session import SessionFactory


def get_database_session() -> Generator[
    Session,
    None,
    None,
]:
    with SessionFactory() as session:
        yield session


DatabaseSession = Annotated[
    Session,
    Depends(get_database_session),
]
