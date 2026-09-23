// Echo server for testing Next.js forwarding, not a replacement for API tests.
const http = require('node:http');
http.createServer((request, response) => {
  let body = '';
  request.on('data', chunk => { body += chunk; });
  request.on('end', () => {
    response.writeHead(200, { 'Content-Type': 'application/json' });
    response.end(JSON.stringify({ path: request.url, method: request.method, body }));
  });
}).listen(8101, '127.0.0.1');
