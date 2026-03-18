import http from "node:http";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const PAGES_DIR = path.join(__dirname, "pages");

const MIME: Record<string, string> = {
  ".html": "text/html; charset=utf-8",
  ".json": "application/json",
  ".css": "text/css",
  ".js": "application/javascript",
};

function serveFile(res: http.ServerResponse, filePath: string): void {
  const ext = path.extname(filePath);
  const contentType = MIME[ext] ?? "text/plain";
  try {
    const content = fs.readFileSync(filePath, "utf-8");
    res.writeHead(200, { "Content-Type": contentType });
    res.end(content);
  } catch {
    res.writeHead(404, { "Content-Type": "text/plain" });
    res.end("404 Not Found");
  }
}

function apiStatus(): object {
  return {
    status: "online",
    version: "0.1.0",
    timestamp: new Date().toISOString(),
    company: {
      health: 87,
      activeTasks: 12,
      mrr: 4200,
      departments: [
        { name: "Engineering", status: "green", tasks: 4 },
        { name: "Marketing", status: "green", tasks: 2 },
        { name: "Sales", status: "yellow", tasks: 3 },
        { name: "Finance", status: "green", tasks: 1 },
        { name: "HR", status: "green", tasks: 0 },
        { name: "Product", status: "green", tasks: 1 },
        { name: "Operations", status: "yellow", tasks: 1 },
        { name: "Legal", status: "green", tasks: 0 },
      ],
    },
  };
}

function handleRequest(
  req: http.IncomingMessage,
  res: http.ServerResponse
): void {
  const url = req.url ?? "/";
  const method = req.method ?? "GET";

  if (method !== "GET") {
    res.writeHead(405, { "Content-Type": "text/plain" });
    res.end("Method Not Allowed");
    return;
  }

  res.setHeader("X-Content-Type-Options", "nosniff");
  res.setHeader("X-Frame-Options", "DENY");

  switch (url) {
    case "/":
      serveFile(res, path.join(PAGES_DIR, "dashboard.html"));
      break;
    case "/license":
      serveFile(res, path.join(PAGES_DIR, "license.html"));
      break;
    case "/raas":
      serveFile(res, path.join(PAGES_DIR, "raas.html"));
      break;
    case "/api/status":
      res.writeHead(200, { "Content-Type": "application/json" });
      res.end(JSON.stringify(apiStatus()));
      break;
    default:
      res.writeHead(404, { "Content-Type": "text/plain" });
      res.end("404 Not Found");
  }
}

export function startServer(port?: number): http.Server {
  const listenPort = port ?? Number(process.env["PORT"] ?? 3333);
  const server = http.createServer(handleRequest);
  server.listen(listenPort, () => {
    console.log(`AgencyOS UI running at http://localhost:${listenPort}`);
  });
  return server;
}

export function stopServer(server: http.Server): void {
  server.close();
}

// Run directly
startServer();
