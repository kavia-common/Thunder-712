const http = require('http');

const PORT = process.env.PORT || 3001;

// PUBLIC_INTERFACE
function requestHandler(req, res) {
  res.writeHead(200, { 'Content-Type': 'text/plain' });
  res.end('Thunder-712 backend service is running.\n');
}

const server = http.createServer(requestHandler);

server.listen(PORT, () => {
  // eslint-disable-next-line no-console
  console.log(`Thunder-712 server listening on port ${PORT}`);
});
