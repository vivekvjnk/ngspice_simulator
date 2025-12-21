# VHL Library Docker Deployment

This guide explains how to run the VHL Library as a Dockerized service.

## Overview

The VHL Library can run in two modes:

1. **Stdio Transport** (default) - For local development, tests, and CI
2. **HTTP Transport** - For Docker deployment and remote access

## Quick Start

### Using Docker Compose (Recommended)

```bash
# Build and start the service
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the service
docker-compose down
```

The library will be available at `http://localhost:8080/mcp`

### Using Docker CLI

```bash
# Build the image
docker build -t vhl-library .

# Run the container
docker run -d \
  --name vhl-library \
  -p 8080:8080 \
  -v vhl-lib:/app/lib \
  vhl-library

# View logs
docker logs -f vhl-library

# Stop the container
docker stop vhl-library
docker rm vhl-library
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `VHL_TRANSPORT` | `http` | Transport type (`stdio` or `http`) |
| `PORT` | `8080` | HTTP server port |
| `VHL_LIBRARY_DIR` | `/app/lib` | Directory for persistent component storage |

## Volume Mounts

- `/app/lib` - Persistent storage for library components

This volume ensures that components added via `add_component` survive container restarts.

## API Endpoint

### MCP over HTTP

**Endpoint:** `POST /mcp`

**Request:** JSON-RPC 2.0 message (MCP protocol)

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/list"
}
```

**Response:** JSON-RPC 2.0 response

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "tools": [...]
  }
}
```

### Health Check

**Endpoint:** `GET /health`

**Response:** `200 OK`

## Using with Librarian Agent

Configure your Librarian Agent to connect to the HTTP endpoint:

```typescript
// Instead of spawning a process, use HTTP client
const mcpClient = new MCPHttpClient("http://localhost:8080/mcp");
await mcpClient.call("add_component", {
  component_name: "MyResistor",
  file_content: "..."
});
```

## Local Development

For local development without Docker, use stdio transport:

```bash
# Run in stdio mode (default when not in Docker)
pnpm run dev
```

## Testing

Run tests using stdio transport:

```bash
pnpm test
```

Tests automatically use stdio transport and don't require Docker.

## Troubleshooting

### Container won't start

Check logs:
```bash
docker logs vhl-library
```

### Port already in use

Change the port mapping:
```bash
docker run -p 9090:8080 vhl-library
```

### Volume data lost

Ensure you're using named volumes:
```bash
docker volume ls
docker volume inspect vhl-lib
```

## Architecture

```
┌──────────────────────────────┐
│   VHL Library MCP Core       │
│                              │
│  - Tool definitions          │
│  - Validation orchestration  │
│  - Filesystem interaction   │
│  - tscircuit execution       │
└──────────────┬───────────────┘
               │
        Transport Adapter
               │
     ┌─────────┴─────────┐
     │                   │
 Stdio               HTTP
 (tests)           (Docker)
```

The core MCP server logic is transport-agnostic. The same codebase supports both stdio and HTTP transports.
