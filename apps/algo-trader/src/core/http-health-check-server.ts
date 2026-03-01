import * as http from 'http';

const VERSION = process.env.npm_package_version ?? '0.1.0';
const PORT = parseInt(process.env.HEALTH_PORT ?? '3000', 10);

let server: http.Server | null = null;
let isReady = false;

export function setReady(ready: boolean): void {
  isReady = ready;
}

export function startHealthServer(): void {
  server = http.createServer((req, res) => {
    if (req.method !== 'GET') {
      res.writeHead(405).end();
      return;
    }

    if (req.url === '/health') {
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({
        status: 'ok',
        uptime: process.uptime(),
        timestamp: new Date().toISOString(),
        version: VERSION,
      }));
      return;
    }

    if (req.url === '/ready') {
      const code = isReady ? 200 : 503;
      res.writeHead(code, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ ready: isReady }));
      return;
    }

    res.writeHead(404).end();
  });

  server.listen(PORT, () => {
    process.stdout.write(`Health server listening on :${PORT}\n`);
  });
}

export function stopHealthServer(): void {
  server?.close();
  server = null;
}
