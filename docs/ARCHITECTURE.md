# Architecture

## Target Architecture

Phoenix 140 follows a layered architecture.

```text
Streamlit UI
    ↓
Services
    ↓
Repositories
    ↓
Database
    ↓
Connectors
```

## Layers

### UI Layer
Located in `app.py` and `pages/`.

Responsibilities:
- Display data
- Collect user input
- Trigger service functions

### Service Layer
Located in `services/`.

Responsibilities:
- Calculate financial metrics
- Generate summaries
- Coordinate repositories and connectors
- Prepare data for UI

### Repository Layer
Located in `repositories/`.

Responsibilities:
- Read/write database records
- Hide SQLAlchemy details from UI and services

### Model Layer
Located in `models/`.

Responsibilities:
- Define database tables
- Represent domain objects

### Connector Layer
Located in `connectors/`.

Responsibilities:
- Moneytree API
- Market data API
- Health data API

### AI Layer
Located in `ai/`.

Responsibilities:
- Monthly review generation
- Investment simulations
- Sell/buy decision support
- Health and life coaching

## Design Principle
The app must be modular enough to replace SQLite with PostgreSQL, rule-based AI with OpenAI API, and manual inputs with external APIs.
