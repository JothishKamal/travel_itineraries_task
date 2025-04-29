# Travel Itinerary System

A backend system for managing travel itineraries for Thailand destinations focusing on Phuket and Krabi regions.

## Features

- SQLAlchemy database models for trip itineraries
- RESTful API endpoints using FastAPI
- MCP server for recommended itineraries
- Seed data for Thailand destinations

## Project Structure

```
travel-itinerary-system/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config/
│   │   ├── __init__.py
│   │   └── config.py   # Ignored by Git
│   ├── database/
│   │   ├── __init__.py
│   │   ├── db.py
│   │   ├── seed_data.json
│   │   └── seed.py
│   ├── models/
│   │   ├── __init__.py
│   │   └── models.py
│   ├── routers/
│   │   ├── __init__.py
│   │   └── itinerary.py
│   └── schemas/
│       ├── __init__.py
│       └── schemas.py
├── server.py           # MCP Server
├── requirements.txt
└── README.md
```

## Installation

1. Clone the repository
2. Create and activate a virtual environment (using uv):

```bash
uv venv
source .venv/bin/activate  
```

3. Install dependencies:

```bash
uv pip install -r requirements.txt
```

## Running the Application

Starting the FastAPI server:

```bash
uvicorn app.main:app --reload
```

Starting the MCP server:

```bash
mcp dev server.py
```

1. Visit http://127.0.0.1:6274
2. Connect
3. Select Tools tab
4. List Tools
5. Select get_recommended_itineraries and enter the number of nights


## API Documentation

Once the server is running, access the API documentation at:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Database Setup

The application uses SQLite by default, but you can configure it to use PostgreSQL by modifying the `DATABASE_URL` in `app/config/config.py`.

To initialize the database with seed data, send a POST request to `/seed-data` endpoint after starting the server.

## API Endpoints

- `GET /itineraries`: Get all itineraries
- `GET /itineraries/{itinerary_id}`: Get a specific itinerary by ID
- `POST /itineraries`: Create a new itinerary

## Entity Relationship Diagram
![Entity Relationship Diagram](https://github.com/user-attachments/assets/5c8b69df-57a1-4720-9302-85bea1568fe1)


