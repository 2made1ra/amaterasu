from pathlib import Path
from types import SimpleNamespace

import pytest
from alembic import command
from alembic.config import Config
from dotenv import load_dotenv
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


_BACKEND_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(_BACKEND_ROOT / ".env")


@pytest.fixture
def sqlite_database_url(tmp_path):
    return f"sqlite:///{tmp_path / 'test.db'}"


@pytest.fixture
def alembic_config(sqlite_database_url):
    config = Config(str(_BACKEND_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(_BACKEND_ROOT / "alembic"))
    config.set_main_option("sqlalchemy.url", sqlite_database_url)
    return config


@pytest.fixture
def migrated_database(alembic_config):
    command.upgrade(alembic_config, "head")
    yield alembic_config
    command.downgrade(alembic_config, "base")


@pytest.fixture
def session_factory(sqlite_database_url, migrated_database):
    engine = create_engine(sqlite_database_url, connect_args={"check_same_thread": False})
    SessionTesting = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    try:
        yield SessionTesting
    finally:
        engine.dispose()


@pytest.fixture
def db_session(session_factory):
    session = session_factory()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def test_user(db_session):
    from app.models.user import User

    user = User(username="tester", hashed_password="hashed", is_admin=True)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def client(session_factory, test_user, tmp_path, monkeypatch):
    from app.api import deps
    from app.core.config import settings
    from app.main import app

    upload_dir = tmp_path / "uploads"
    monkeypatch.setattr(settings, "UPLOAD_DIR", str(upload_dir))

    def override_get_db():
        db = session_factory()
        try:
            yield db
        finally:
            db.close()

    def override_get_current_user():
        return SimpleNamespace(id=test_user.id, username=test_user.username, is_admin=test_user.is_admin)

    app.dependency_overrides[deps.get_db] = override_get_db
    app.dependency_overrides[deps.get_current_user] = override_get_current_user

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
