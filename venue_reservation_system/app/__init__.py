from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///reservations.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.secret_key = 'dev_secret_key' # Add this for flash messaging

    db.init_app(app)

    with app.app_context():
        # Import models here so Flask-SQLAlchemy can register them
        from app import models # This will trigger imports in app/models/__init__.py
        from app.services import reservation_service # Import service for populate function

        # Import routes here to avoid circular imports
        from app.routes import main_routes
        from app.routes import venue_routes
        from app.routes import reservation_routes
        from app.routes import stats_routes # New import

        app.register_blueprint(main_routes.bp)
        app.register_blueprint(venue_routes.bp)
        app.register_blueprint(reservation_routes.bp)
        app.register_blueprint(stats_routes.bp) # Register the new blueprint

        # Create database tables if they don't exist
        db.create_all()
        # Consider calling populate_default_reservation_settings() here once
        # or provide a CLI command for it. For simplicity, call it here for now.
        # This ensures settings are present when the app starts.
        if app.config.get('ENV') != 'testing': # Avoid running during tests if it causes issues
             reservation_service.populate_default_reservation_settings()

    return app
