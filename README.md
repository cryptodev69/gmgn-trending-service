# GMGN Trending Service

A comprehensive web service for analyzing trending tokens on Solana using GMGN.ai data.

## Features

- **Trending Tokens**: Get trending tokens for various timeframes (1m, 5m, 1h, 6h, 24h).
- **New Pairs**: specific endpoint for newly listed pairs.
- **Smart Wallets**: Track trending wallets and get wallet details.
- **Token Analysis**: Get price, top buyers, security info, and bonding curve progress.
- **Chain Info**: Real-time gas fees.
- **Docker Support**: Fully containerized for easy deployment.

## API Documentation

Once the service is running, you can access the interactive API documentation at:

- Swagger UI: `http://localhost:8000/api/v1/docs`
- ReDoc: `http://localhost:8000/api/v1/redoc`

## Getting Started

### Prerequisites

- Docker and Docker Compose
- Python 3.9+ (for local development)

### Running with Docker

```bash
docker-compose up --build
```

The service will be available at `http://localhost:8000`.

### Running Locally

1. Create a virtual environment:
    ```bash
    python -m venv venv
    source venv/bin/activate
    ```

2. Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

3. Run the application:
    ```bash
    uvicorn app.main:app --reload
    ```

## Project Structure

- `app/`: Main application source code.
  - `api/`: API endpoints and router configuration.
  - `core/`: Core configuration and settings.
  - `services/`: External services integration (GMGN client).
  - `models/`: Data models (Pydantic schemas).
- `Dockerfile`: Docker build instructions.
- `docker-compose.yml`: Docker composition for development.

## Endpoints

### Market
- `GET /api/v1/market/pairs/new`: Get new pairs.
- `GET /api/v1/market/tokens/trending`: Get trending tokens.
- `GET /api/v1/market/tokens/pump-completion`: Get tokens by bonding curve progress.
- `GET /api/v1/market/tokens/sniped`: Get recently sniped tokens.

### Tokens
- `GET /api/v1/tokens/{address}/info`: Get token details.
- `GET /api/v1/tokens/{address}/price`: Get real-time price.
- `GET /api/v1/tokens/{address}/top-buyers`: Get top buyers.
- `GET /api/v1/tokens/{address}/security`: Get security report.

### Wallets
- `GET /api/v1/wallets/trending`: Get trending wallets.
- `GET /api/v1/wallets/{address}`: Get wallet analysis.

### Chain
- `GET /api/v1/chain/gas`: Get Solana gas fees.

## License

MIT
