import {
  PROJECT_ROOT,
  LOCAL_LIBRARY_DIR,
  TEMP_DIR
} from "./config/paths.js";
import { runServer } from "./mcp/server.js";

console.log("PROJECT_ROOT:", PROJECT_ROOT);
console.log("LOCAL_LIBRARY_DIR:", LOCAL_LIBRARY_DIR);
console.log("TEMP_DIR:", TEMP_DIR);

runServer().catch((err) => {
  console.error("MCP server failed:", err);
  process.exit(1);
});
