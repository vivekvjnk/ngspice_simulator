import { server } from "../../src/mcp/server.js";
import {
  ListToolsRequestSchema,
  CallToolRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";

describe("MCP Server (thin transport)", () => {
  test("lists all expected tools", async () => {
    const response = await server.handleRequest({
      jsonrpc: "2.0",
      id: 1,
      method: ListToolsRequestSchema.method,
      params: {},
    });

    expect(response).toBeDefined();
    expect(response.result).toBeDefined();

    const toolNames = response.result.tools.map(
      (t: any) => t.name
    );

    expect(toolNames).toEqual(
      expect.arrayContaining([
        "add_component",
        "list_local_components",
        "search_library",
      ])
    );
  });

  test("routes add_component tool call", async () => {
    const response = await server.handleRequest({
      jsonrpc: "2.0",
      id: 2,
      method: CallToolRequestSchema.method,
      params: {
        name: "add_component",
        arguments: {
          component_name: "MCPTestComponent",
          file_content: `
            export const MCPTestComponent = () => null;
          `,
        },
      },
    });

    expect(response).toBeDefined();
    expect(response.result).toBeDefined();

    const content = response.result.content[0];
    expect(content.type).toBe("json");
    expect(content.json.success).toBe(true);
  });

  test("routes list_local_components tool call", async () => {
    const response = await server.handleRequest({
      jsonrpc: "2.0",
      id: 3,
      method: CallToolRequestSchema.method,
      params: {
        name: "list_local_components",
        arguments: {},
      },
    });

    expect(response).toBeDefined();
    expect(response.result).toBeDefined();

    const content = response.result.content[0];
    expect(content.type).toBe("json");
    expect(Array.isArray(content.json)).toBe(true);
  });

  test("routes search_library tool call", async () => {
    const response = await server.handleRequest({
      jsonrpc: "2.0",
      id: 4,
      method: CallToolRequestSchema.method,
      params: {
        name: "search_library",
        arguments: {
          query: "res",
          mode: "fuzzy",
          depth: "surface",
        },
      },
    });

    expect(response).toBeDefined();
    expect(response.result).toBeDefined();

    const content = response.result.content[0];
    expect(content.type).toBe("json");
    expect(Array.isArray(content.json)).toBe(true);
  });
});
