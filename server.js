//
// PUBLIC_INTERFACE
/**
 * Entry point for Thunder-712 backend service.
 * Binds an HTTP server to process.env.PORT (default 3001).
 *
 * Set the PORT in your .env file or via environment variable.
 */
const http = require('http');
require('dotenv').config();

const PORT = process.env.PORT || 3001;

const requestListener = (req, res) => {
  res.writeHead(200);
  res.end('Thunder-712 server running');
};

const server = http.createServer(requestListener);

server.listen(PORT, () => {
  console.log(`Thunder-712 server listening on port ${PORT}`);
});
