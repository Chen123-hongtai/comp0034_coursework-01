# Global Tourism Recovery Dashboard (Full Stack)

## Overview
This project now includes:
- A Dash front-end web app
- A FastAPI back-end REST API
- SQLite data storage accessed through SQLModel ORM

The front-end pages fetch data from REST routes (with graceful fallback if API is not running).

## Tech Stack
- Python 3.12+
- Dash
- FastAPI
- SQLModel / SQLAlchemy
- SQLite
- Pytest

## Install
```bash
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[test]"
```

## Run the Back-end API
```bash
fastapi dev backend/main.py
```
Default API base URL: `http://127.0.0.1:8000`

## Run the Front-end App
In a second terminal:
```bash
python app.py
```
Dash URL: `http://localhost:8050`

If your API is running on a different host/port, set:
```bash
set TOURISM_API_BASE_URL=http://127.0.0.1:8000
```

## Run Tests
```bash
python -m pytest
```

## API Docs
After starting FastAPI:
- Swagger UI: `http://127.0.0.1:8000/docs`
