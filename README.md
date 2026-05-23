# Micro-Decentro

A production-grade REST API that simulates core "Ledgers" and "Global Payouts" infrastructure.

## Features
- Virtual Account Management
- Payouts (Transfers) between accounts
- Row-level database locking for concurrent transaction safety
- Idempotency via `Idempotency-Key` headers
- Rate Limiting (100 req/min)
- Security: API Keys required (`X-API-Key`)
- OpenAPI/Swagger Documentation

## Setup Instructions

### 1. Prerequisites
Ensure you have Python 3.11+ installed.
```bash
python -m venv .venv
.venv\Scripts\activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the Server
```bash
python app.py
```
This will automatically create the `micro_decentro.db` SQLite database if it doesn't exist.

### 4. API Documentation (Swagger)
Open your browser and navigate to:
[http://localhost:5000/api-docs](http://localhost:5000/api-docs)

To test the endpoints in Swagger UI, click **Authorize** and enter the dummy API Key:
`decentro-secret-key-2026`

### 5. Running Tests
You can run the full test suite using `pytest`:
```bash
pytest tests/test_api.py -v
```
