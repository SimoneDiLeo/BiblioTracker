import pytest
import asyncio
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool # Use StaticPool for SQLite in-memory or file-based for tests

from main import app # Main FastAPI application
from database.database_setup import Base, SQLALCHEMY_DATABASE_URL as MAIN_SQLALCHEMY_DATABASE_URL
from auth.auth_handler import get_db # The dependency we need to override

# --- Test Database Configuration ---
# Use a different database for testing (in-memory SQLite or a test file)
TEST_SQLALCHEMY_DATABASE_URL = "sqlite:///./test_ris.db"
# TEST_SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:" # In-memory option

# Create a test engine
engine_test = create_engine(
    TEST_SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}, # Needed for SQLite file-based
    poolclass=StaticPool # Recommended for SQLite testing to ensure same connection
)

# Create a test session local
SessionLocal_test = sessionmaker(autocommit=False, autoflush=False, bind=engine_test)

# --- Fixtures ---

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test session."""
    # For pytest-asyncio: if you need to change loop policy or use a different loop.
    # For most cases, pytest-asyncio handles this automatically.
    # This fixture is mainly to ensure an event loop is available for session-scoped async fixtures if any.
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
def engine_test_fixture():
    """Yields the test engine instance."""
    return engine_test

@pytest.fixture(scope="function") # Changed to function scope for cleaner tests
def init_test_db(engine_test_fixture):
    """
    Initializes the test database. Drops all tables and recreates them.
    This runs before each test function.
    """
    Base.metadata.drop_all(bind=engine_test_fixture)
    Base.metadata.create_all(bind=engine_test_fixture)
    yield # Test runs here
    # Teardown can be added here if needed after each test,
    # but drop_all/create_all at the start of each test ensures isolation.

@pytest.fixture(scope="function")
def db_session_test(init_test_db): # Depends on init_test_db to ensure DB is clean
    """
    Provides a test database session. Rolls back any changes after the test.
    """
    connection = engine_test.connect()
    transaction = connection.begin()
    session = SessionLocal_test(bind=connection)
    
    yield session  # Provide the session to the test
    
    session.close()
    transaction.rollback() # Rollback any changes made during the test
    connection.close()

# --- Override FastAPI app dependencies ---

def override_get_db():
    """
    Overrides the get_db dependency for testing.
    Uses the test database session.
    """
    connection = engine_test.connect() # Get a connection from the test engine
    # Begin a transaction for this connection. This is not strictly necessary for each
    # individual override_get_db call if the test client handles transactions,
    # but it's good for ensuring a consistent transactional state if used directly.
    # transaction = connection.begin() 
    
    db = SessionLocal_test(bind=connection) # Create a session bound to this connection
    try:
        yield db
    finally:
        db.close()
        connection.close() # Ensure connection is closed after the request

# Apply the override to the FastAPI app
app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="function")
def client(init_test_db): # init_test_db ensures DB is fresh for each test
    """
    Provides a TestClient instance for making API requests to the FastAPI app,
    with the database dependency overridden.
    """
    # The app's get_db dependency is already overridden globally for tests.
    # TestClient uses the globally configured app.
    with TestClient(app) as c:
        yield c

# --- Test utilities ---
@pytest.fixture(scope="function")
def test_user_data():
    return {"username": "testuser", "email": "test@example.com", "password": "testpassword"}

@pytest.fixture(scope="function")
def registered_test_user(client, test_user_data):
    """Registers a new user and returns the response data."""
    response = client.post("/api/users/register", json=test_user_data)
    assert response.status_code == 201 # Ensure user registration is successful
    return response.json() # Return created user's public data

@pytest.fixture(scope="function")
def authenticated_test_user_tokens(client, test_user_data, registered_test_user):
    """Logs in the test user and returns access tokens."""
    # registered_test_user fixture ensures user exists
    login_data = {"username": test_user_data["username"], "password": test_user_data["password"]}
    response = client.post("/api/users/login", data=login_data) # form data for login
    assert response.status_code == 200
    return response.json() # {"access_token": "...", "token_type": "bearer"}

@pytest.fixture(scope="function")
def authenticated_headers(authenticated_test_user_tokens):
    """Returns headers for an authenticated request."""
    token = authenticated_test_user_tokens["access_token"]
    return {"Authorization": f"Bearer {token}"}
