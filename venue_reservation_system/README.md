# Venue Reservation System

A Flask-based application for managing venue reservations. This system allows for venue administration, setting availability, handling special dates, and processing teacher reservations. It also includes basic statistics and conflict logging.

## Features (Implemented)

-   **Venue Management**: Create, read, update, and delete venues. Set venue capacity, description, equipment details, and usage notes.
-   **Availability Management**: Define regular opening hours for each venue for different days of the week.
-   **Special Dates**: Set specific dates as closed or with special operating hours (e.g., holidays).
-   **Reservation Rules**: Configurable booking window (e.g., book up to 7 days in advance) and time slot duration (e.g., 30 or 60 minutes).
-   **Teacher Reservations**:
    -   Query available time slots for venues.
    -   Create new reservations with conflict detection.
    -   View personal reservation history.
    -   Cancel reservations (with rules, e.g., before start time).
-   **Statistics**:
    -   Logging of attempted conflicting reservations.
    -   Basic API for venue usage summary (total bookings, hours booked).
-   **Basic UI**: A simple web interface to view venues, check availability, and make reservations.
-   **Testing**: Comprehensive unit and integration test suite.

## Project Structure

-   `app/`: Main application package.
    -   `models/`: SQLAlchemy database models.
    -   `routes/`: API and UI route blueprints.
        - `main_routes.py`: UI routes and basic API root.
        - `venue_routes.py`: Venue, Availability, Special Date APIs.
        - `reservation_routes.py`: Reservation APIs.
        - `stats_routes.py`: Statistics APIs.
    -   `services/`: Business logic (e.g., `reservation_service.py`).
    -   `static/`: Static files (CSS, JS - currently minimal).
    -   `templates/`: HTML templates for the UI.
    -   `__init__.py`: Flask application factory.
-   `tests/`: Unit and integration tests.
    - `conftest.py`: Pytest fixtures.
    - `unit/`: Unit tests for models and services.
    - `integration/`: Integration tests for API endpoints.
-   `run.py`: Script to run the Flask development server.
-   `requirements.txt`: Python dependencies.
-   `reservations.db`: SQLite database file (created when the app runs).

## Setup and Installation

1.  **Prerequisites**:
    -   Python (3.8+ recommended).
    -   `pip` for installing packages.
    -   (Optional) A virtual environment tool like `venv` or `conda`.

2.  **Clone the Repository** (if applicable, otherwise ensure you are in the project root `venue_reservation_system`):
    ```bash
    # git clone <repository_url>
    # cd venue_reservation_system
    ```

3.  **Create and Activate a Virtual Environment** (Recommended):
    ```bash
    python -m venv venv
    # On Windows
    # venv\Scripts\activate
    # On macOS/Linux
    # source venv/bin/activate
    ```

4.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

5.  **Run the Application**:
    ```bash
    python run.py
    ```
    The application will typically start on `http://127.0.0.1:5000/`.
    - The basic UI can be accessed at `http://127.0.0.1:5000/`.
    - API endpoints are available under `/api/...`.

## Running Tests

To run the automated test suite:

1.  Ensure all development dependencies are installed (including `pytest` and `pytest-flask` from `requirements.txt`).
2.  Navigate to the project root directory (`venue_reservation_system`).
3.  Run pytest:
    ```bash
    pytest
    ```
    Or, to run as a module (if `pytest` command is not directly found):
    ```bash
    python -m pytest
    ```

## Basic API Overview

The API is organized into several blueprints:

-   **Venues (`/api/venues/`)**: For managing venues, their availability, and special dates. Supports CRUD operations.
-   **Reservations (`/api/reservations/`)**: For querying available slots, creating, viewing, and cancelling reservations. User context for creating/viewing own reservations is typically expected (e.g., via a header like `X-User-Id: <user_id>`).
-   **Statistics (`/api/stats/`)**: For retrieving usage statistics and conflict information.

For detailed API endpoint definitions, please refer to the files in the `app/routes/` directory. Key models defining the data structures are in `app/models/`.

## Placeholder User Authentication

Currently, user-specific API endpoints (like creating a reservation or viewing "my reservations") use a placeholder mechanism for user identification. This typically involves an `X-User-Id` header. For testing, user ID `1` is often assumed or created if not present. This is not a production-ready authentication system.
