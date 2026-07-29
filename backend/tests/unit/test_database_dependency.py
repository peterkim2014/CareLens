from collections.abc import Generator
from unittest.mock import MagicMock, patch

from sqlalchemy.orm import Session

from app.api.dependencies.database import get_database_session


def test_database_dependency_yields_session() -> None:
    session = MagicMock(spec=Session)
    context_manager = MagicMock()

    context_manager.__enter__.return_value = session
    context_manager.__exit__.return_value = None

    with patch(
        "app.api.dependencies.database.SessionFactory",
        return_value=context_manager,
    ):
        dependency = get_database_session()

        yielded_session = next(dependency)

        assert yielded_session is session

        try:
            next(dependency)
        except StopIteration:
            pass
        else:
            raise AssertionError(
                "Database dependency should yield exactly once",
            )

    context_manager.__exit__.assert_called_once()


def test_database_dependency_closes_session_after_generator_close() -> None:
    session = MagicMock(spec=Session)
    context_manager = MagicMock()

    context_manager.__enter__.return_value = session
    context_manager.__exit__.return_value = None

    with patch(
        "app.api.dependencies.database.SessionFactory",
        return_value=context_manager,
    ):
        dependency: Generator[Session, None, None] = get_database_session()

        yielded_session = next(dependency)

        assert yielded_session is session

        dependency.close()

    context_manager.__exit__.assert_called_once()
