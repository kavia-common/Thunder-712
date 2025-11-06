'use strict';

/**
 * Minimal HTTP server to provide a clear start command for preview environments.
 * Listens on process.env.PORT or 3001, binding to 0.0.0.0.
 */

const http = require('http');

/**
 * Creates a simple HTTP server with two routes:
 *   - GET /        : returns a friendly text message
 *   - GET /health  : returns a JSON health status
 *
 * PUBLIC_INTERFACE
 * @returns {http.Server} A configured HTTP server instance.
 */
function createServer() {
  const server = http.createServer((req, res) => {
    try {
      const reqUrl = new URL(req.url, 'http://localhost');
      const path = reqUrl.pathname;

      // Basic routing
      if (req.method === 'GET' && (path === '/' || path === '')) {
        res.writeHead(200, {
          'Content-Type': 'text/plain; charset=utf-8',
          'Cache-Control': 'no-store',
        });
        res.end('Thunder-712 preview server is running.\nUse GET /health for a JSON health response.\n');
        return;
      }

      if (req.method === 'GET' && path === '/health') {
        const payload = JSON.stringify({ status: 'ok', service: 'Thunder-712', uptimeSec: process.uptime() });
        res.writeHead(200, {
          'Content-Type': 'application/json; charset=utf-8',
          'Cache-Control': 'no-store',
        });
        res.end(payload);
        return;
      }

      // Fallback 404
      res.writeHead(404, { 'Content-Type': 'text/plain; charset=utf-8' });
      res.end('Not Found');
    } catch (err) {
      // Safety net for any unexpected error
      console.error('[server] Unhandled error:', err);
      res.writeHead(500, { 'Content-Type': 'text/plain; charset=utf-8' });
      res.end('Internal Server Error');
    }
  });

  return server;
}

/**
 * Starts the HTTP server on the desired host/port.
 *
 * PUBLIC_INTERFACE
 * @param {number} [port] Optional override of the listening port.
 * @param {string} [host] Optional override of the bind host (defaults to 0.0.0.0).
 * @returns {http.Server} The started server instance.
 */
function startServer(port, host) {
  const PORT = Number.isInteger(port) ? port : parseInt(process.env.PORT || '3001', 10);
  const HOST = host || '0.0.0.0';

  const server = createServer();

  server.on('error', (err) => {
    console.error(`[server] Error: ${err && err.message ? err.message : err}`);
    process.exitCode = 1;
  });

  server.listen(PORT, HOST, () => {
    console.log(`[server] Listening on http://${HOST}:${PORT}`);
  });

  // Graceful shutdown handlers (optional but helpful in preview infra)
  const shutdown = () => {
    console.log('[server] Shutting down...');
    server.close(() => {
      process.exit(0);
    });

    // Force exit if close hangs
    setTimeout(() => process.exit(0), 1500).unref();
  };

  process.on('SIGTERM', shutdown);
  process.on('SIGINT', shutdown);

  return server;
}

// Start automatically if invoked directly.
if (require.main === module) {
  startServer();
}

// Export for potential reuse/testing.
module.exports = { createServer, startServer };
