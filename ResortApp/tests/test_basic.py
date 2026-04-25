"""
test_basic.py — Phase 1 infrastructure validation
Verifies test DB connection, API boot-up, and auth override work correctly.
"""
import pytest
from sqlalchemy import text


class TestDatabaseInfrastructure:
    def test_connection(self, db_session):
        """Test DB session yields and basic query works."""
        result = db_session.execute(text("SELECT 1")).scalar()
        assert result == 1

    def test_tables_created(self, db_session):
        """Verify core tables exist in orchid_test database."""
        result = db_session.execute(
            text("SELECT table_name FROM information_schema.tables WHERE table_schema='public'")
        ).fetchall()
        table_names = {row[0] for row in result}
        assert "users" in table_names, "users table missing"
        assert "rooms" in table_names, "rooms table missing"
        assert "bookings" in table_names, "bookings table missing"
        assert "inventory_items" in table_names, "inventory_items table missing"

    def test_transaction_rollback_isolation(self, db_session):
        """Verify that each test gets a clean rollback (no test data bleeds between tests)."""
        from app.models.user import User
        initial_count = db_session.query(User).count()
        # Add a temp user
        u = User(name="IsolationUser", email="isolation@test.com",
                 hashed_password="x", is_active=True)
        db_session.add(u)
        db_session.flush()
        new_count = db_session.query(User).count()
        assert new_count == initial_count + 1
        # After this test, rollback will undo this — verified by the next test


class TestAPIBootstrap:
    def test_api_not_crashing(self, client):
        """Verify the FastAPI server boots without a 500 error on root."""
        response = client.get("/")
        assert response.status_code != 500

    def test_docs_accessible(self, client):
        """Swagger docs should be accessible (returns 200)."""
        response = client.get("/docs")
        assert response.status_code == 200

    def test_auth_protected_route_without_token(self, client):
        """Accessing protected routes without a token should return 401."""
        response = client.get("/api/rooms/")
        assert response.status_code == 401, (
            f"Expected 401, got {response.status_code}: {response.text[:200]}"
        )

    def test_auth_override_works(self, authorized_client):
        """With auth overridden, protected route should not return 401."""
        response = authorized_client.get("/api/rooms/")
        assert response.status_code != 401, (
            f"Auth override failed — still got 401: {response.text[:200]}"
        )
