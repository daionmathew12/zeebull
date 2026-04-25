import os
import pytest
from typing import Generator, Optional
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# ─────────────────────────────────────────────────────
# Must set env variables BEFORE importing app modules
# ─────────────────────────────────────────────────────
os.environ["DATABASE_URL"] = "postgresql+psycopg2://postgres:qwerty123@localhost/orchid_test"

from app.database import Base, get_db
from main import app
from app.models.user import User, Role
from app.utils.auth import get_current_user, get_branch_id as get_branch_id_auth, get_db as get_db_auth
from app.utils.branch_scope import get_branch_id as get_branch_id_scope
from app.models.branch import Branch

# ─────────────────────────────────────────────────────
# Test Engine — points to orchid_test database
# ─────────────────────────────────────────────────────
TEST_DATABASE_URL = "postgresql+psycopg2://postgres:qwerty123@localhost/orchid_test"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"sslmode": "disable", "connect_timeout": 10},
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Creates all database tables in orchid_test before the session."""
    Base.metadata.create_all(bind=test_engine)
    yield
    # Optionally tear down: Base.metadata.drop_all(bind=test_engine)


@pytest.fixture()
def db_session() -> Generator:
    """Provides a fresh, isolated SQLAlchemy session per test."""
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()  # Roll back everything — guaranteed fresh state
        connection.close()


@pytest.fixture()
def test_branch(db_session) -> Branch:
    """Creates a default test branch."""
    branch = Branch(name="Test Branch", code="TB")
    db_session.add(branch)
    db_session.flush()
    return branch


@pytest.fixture()
def test_role(db_session) -> Role:
    """Creates a default admin role."""
    role = Role(name="admin", permissions="rooms:view,rooms:create,rooms:edit,rooms:delete,inventory:view,inventory:edit,bill:view,bill:create")
    db_session.add(role)
    db_session.flush()
    return role


@pytest.fixture()
def mock_superadmin(db_session, test_branch, test_role) -> User:
    """Creates and persists a real superadmin user in the test DB."""
    from app.utils.auth import get_password_hash

    # Clean up any existing test user first
    existing = db_session.query(User).filter(User.email == "test_admin@orchid.com").first()
    if existing:
        db_session.delete(existing)
        db_session.flush()

    user = User(
        name="Test Admin",
        email="test_admin@orchid.com",
        hashed_password=get_password_hash("TestPass@123"),
        is_active=True,
        is_superadmin=True,
        branch_id=test_branch.id,
        role_id=test_role.id
    )
    db_session.add(user)
    db_session.flush()
    return user


@pytest.fixture()
def client(db_session) -> Generator:
    """FastAPI TestClient with the database dependency overridden to the test session."""
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_db_auth] = override_get_db
    
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def authorized_client(client, mock_superadmin) -> TestClient:
    """TestClient whose get_current_user and get_branch_id are mocked to the test superadmin."""
    app.dependency_overrides[get_current_user] = lambda: mock_superadmin
    # Using real get_branch_id which respects headers and falls back to user.branch_id
    yield client
    # Clear is handled by client fixture


def make_auth_token(user: User) -> str:
    """Generate a real JWT token for a given user (useful for headers)."""
    from app.utils.auth import create_access_token
    return create_access_token({"user_id": user.id})
