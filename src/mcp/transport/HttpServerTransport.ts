import express, { Request, Response } from "express";
import { Transport } from "@modelcontextprotocol/sdk/shared/transport.js";
import { JSONRPCMessage } from "@modelcontextprotocol/sdk/types.js";

export class HttpServerTransport implements Transport {
    private app: express.Express;
    private port: number;
    private pendingRequests = new Map<string | number, Response>();
    private server: any; // Store the http server instance to close it later

    onclose?: () => void;
    onerror?: (error: Error) => void;
    onmessage?: (message: JSONRPCMessage) => void;

    constructor(port: number = 8080) {
        this.app = express();
        this.port = port;
        this.app.use(express.json());

        this.app.post("/mcp", (req, res) => {
            this.handleRequest(req, res);
        });

        // Health check
        this.app.get("/health", (req, res) => {
            res.status(200).send("OK");
        });
    }

    private handleRequest(req: Request, res: Response) {
        const message = req.body as JSONRPCMessage;
        if (!message) {
            res.status(400).send("Invalid JSON-RPC message");
            return;
        }

        if (message.jsonrpc !== "2.0") {
            res.status(400).send("Invalid JSON-RPC version");
            return;
        }

        // For request/response, we need to track the ID
        // Type guard: JSONRPCMessage can be Request, Response, or Notification
        // Only Request and Response have an 'id' property
        const messageWithId = message as any;
        if (messageWithId.id !== undefined && messageWithId.id !== null) {
            this.pendingRequests.set(messageWithId.id, res);

            // Set a timeout to clean up if no response comes?
            // MCP server should respond fairly quickly, but good to have safety.
            // For now, rely on server responding.
        } else {
            // Notification. Send 202 Accepted immediately.
            res.status(202).send();
        }

        if (this.onmessage) {
            this.onmessage(message);
        }
    }

    async start(): Promise<void> {
        return new Promise((resolve) => {
            this.server = this.app.listen(this.port, "0.0.0.0", () => {
                console.log(`MCP HTTP Server listening on port ${this.port}`);
                resolve();
            });
        });
    }

    async close(): Promise<void> {
        if (this.server) {
            this.server.close();
        }
        if (this.onclose) {
            this.onclose();
        }
    }

    async send(message: JSONRPCMessage): Promise<void> {
        const messageWithId = message as any;
        if (messageWithId.id !== undefined && messageWithId.id !== null) {
            const res = this.pendingRequests.get(messageWithId.id);
            if (res) {
                res.json(message);
                this.pendingRequests.delete(messageWithId.id);
            } else {
                console.warn(`No pending request found for ID ${messageWithId.id}`);
            }
        } else {
            // Notification from server to client.
            // We can't send this over HTTP request/response unless we have a pending request.
            // But notifications don't have IDs, so we can't match them.
            // Just log it.
            console.log("Server sent notification (dropped due to stateless HTTP):", message);
        }
    }
}
