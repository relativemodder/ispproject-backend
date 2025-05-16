# ISP Project API

## Running the API

This project uses FastAPI with SQLAlchemy ORM and SQLite (default).

To run the API locally:

1. Install dependencies (using uv):
```
uv sync
```

2. Start the API server:
```
uv run fastapi dev src/main.py
```

3. Open your browser and navigate to:
```
http://localhost:8000/docs
```
to access the interactive API documentation.

## Project Structure

- `src/db.py`: Database connection and session management.
- `src/models.py`: ORM models for orders, installers, comments, and statuses.
- `src/routers/orders.py`: API endpoints for order management.
- `src/main.py`: FastAPI app initialization and router inclusion.

## Features

- Create, view, update orders.
- Assign installers to orders.
- Change order status.
- Add comments to orders.

Future improvements:
- Add authentication and authorization.
- Add routers for installers and comments separately.
- Support for MariaDB/Postgres.
