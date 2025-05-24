import pytest
from app import create_app, db
from app.models import User, Venue, ReservationSettings # Add other models as needed for setup
from app.services.reservation_service import populate_default_reservation_settings

@pytest.fixture(scope='session')
def app():
    # Create a Flask app configured for testing
    app = create_app()
    app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",  # Use in-memory SQLite for tests
        "WTF_CSRF_ENABLED": False, # Disable CSRF for forms if you have them and test them
        "SECRET_KEY": "test_secret_key" 
    })
    
    with app.app_context():
        db.create_all()
        # Populate essential initial data, e.g., default reservation settings
        populate_default_reservation_settings()

        # You might want to create a default user or venue for many tests
        # For example:
        # if not User.query.get(1):
        #     default_user = User(id=1, username='testuserfixture')
        #     db.session.add(default_user)
        #     db.session.commit()

    yield app

    # Teardown: drop all tables after the session
    # with app.app_context():
    #     db.drop_all() # This might not be needed with in-memory, but good for other DBs

@pytest.fixture()
def client(app):
    # Test client for making requests to the app
    return app.test_client()

@pytest.fixture(scope='function') # Use 'function' scope to get a fresh DB for each test
def init_database(app):
    # This fixture can be used to ensure a clean database state for each test function.
    # It's called for its side effects (db operations).
    with app.app_context():
        db.drop_all() # Ensure tables are clean before each test
        db.create_all()
        populate_default_reservation_settings() # Repopulate basic settings

        # Create a default user for convenience in tests that require a user
        user = User.query.get(1)
        if not user:
            default_user = User(id=1, username='testuser_fixture')
            db.session.add(default_user)
            db.session.commit()
        
        # You can add more default data here if needed by many tests
        # e.g., a default venue
        # venue = Venue.query.get(1)
        # if not venue:
        #     default_venue = Venue(id=1, name='Test Venue', capacity=10)
        #     db.session.add(default_venue)
        #     db.session.commit()


    yield db # Not strictly necessary to yield db, but can be useful

    # Teardown after each test function if needed, though in-memory DB usually resets.
    # with app.app_context():
    #     db.session.remove()
    #     db.drop_all()

# Fixture to make the db session available to tests if they need to interact directly
@pytest.fixture()
def db_session(app, init_database): # Depends on init_database to ensure clean state
     with app.app_context():
        yield db.session
