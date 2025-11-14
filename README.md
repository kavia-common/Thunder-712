# Thunder-712

A multi-repository project likely providing backend infrastructure and common services for enterprise applications.

## Running the Service

1. Copy `.env.example` to `.env` and adjust values as needed:
   ```sh
   cp .env.example .env
   ```
   Set the desired `PORT` value in `.env` (default: 3001).

2. Install dependencies:
   ```sh
   npm install
   ```

3. Start the server:
   ```sh
   npm start
   ```
   The server will listen on the port specified in your `.env` or default to 3001.

## Environment Variables

- `PORT`: The port number for the HTTP server to listen on (default: 3001).
