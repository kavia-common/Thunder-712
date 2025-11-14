# Thunder-712 Backend Service

This is a minimal Node.js Express backend server for the Thunder-712 container. It exposes health and basic API endpoints and is ready for integration with the entservices-infra-712 service as needed.

## Features

- Health endpoint: `/health`
- Example API route: `/api/info`
- Environment variable support
- Ready-to-use start script

## Getting Started

1. **Install Node.js** (version 14 or higher recommended).

2. **Install dependencies:**  
   ```sh
   npm install
   ```

3. **Configure environment:**  
   Copy `.env.example` to `.env` and adjust variables as needed:
   ```sh
   cp .env.example .env
   ```

4. **Run the server:**  
   ```sh
   npm start
   ```

   By default, the server listens on the port defined in the `PORT` environment variable (defaults to 3001).

## Endpoints

- `GET /health`  
  Returns `{ "status": "ok" }` for health checks.

- `GET /api/info`  
  Returns service metadata and dependency placeholder info.

## Notes

- Placeholder for integration with [entservices-infra-712] via `ENTSERVICES_INFRA_URL`.  
  The server runs independently even if that service is absent.

## License

[Apache-2.0](./LICENSE)
