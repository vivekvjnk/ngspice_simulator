import fs from "fs/promises";
import path from "path";
import { spawn, ChildProcessWithoutNullStreams } from "child_process";
import crypto from "crypto";
import { IMPORTS_DIR } from "../../config/paths.js";

export type ResolveResult =
  | {
    status: "resolved";
    component: string;
    path: string;
  }
  | {
    status: "selection_required";
    options: string[];
  }
  | {
    status: "no_results";
    message: string;
  }
  | {
    status: "error";
    message: string;
  };

interface ImportSession {
  proc: ChildProcessWithoutNullStreams;
  options: string[];
}

const sessions = new Map<string, ImportSession>();

async function resolveLocal(query: string): Promise<string | null> {
  try {
    const files = await fs.readdir(IMPORTS_DIR);

    const match = files.find(f =>
      f.toLowerCase().includes(query.toLowerCase()) &&
      f.endsWith(".tsx")
    );

    return match ? path.join(IMPORTS_DIR, match) : null;
  } catch {
    return null;
  }
}

function startImport(query: string): Promise<{ sessionId: string; options: string[] }> {
  return new Promise((resolve, reject) => {
    const proc = spawn("tsci", ["import", query], {
      cwd: process.cwd(),
      stdio: "pipe",
    });

    console.log("Searching for: ", query, "...");
    let buffer = "";
    const options = new Set<string>();

    // If the process can't start or crashes
    proc.on("error", (err) => {
      reject(err); // This triggers the .catch() or try/catch block of the caller
    });

    proc.stdout.on("data", (chunk) => {
      const text = chunk.toString();
      buffer += text;
      console.log("tsci stdout:", text);
      if (buffer.includes("No results found matching your query.")) {
        resolve({ sessionId: "no_results", options: [] });
      }

      // crude but stable extraction
      buffer.split("\n").forEach(line => {
        const m = line.match(/^\s*[-*↓]?\s*([A-Za-z0-9_:@\/\.-]+)(?:\s+-.*)?$/);
        if (m) options.add(m[1]);
      });

      if (options.size > 0) {
        const sessionId = crypto.randomUUID();
        sessions.set(sessionId, { proc, options: [...options] });
        console.log("Options found:", [...options]);
        resolve({ sessionId, options: [...options] });
      }
    });

    proc.stderr.on("data", (chunk) => {
      console.error(`tsci stderr: ${chunk}`);
    });

    proc.on("exit", (code) => {
      console.log("tsci exit:", code);
      if (buffer.includes("No results found matching your query.")) {
        resolve({ sessionId: "no_results", options: [] });
      }
      if (options.size === 0) {
        reject(new Error(`startImport: tsci exited with code ${code} and no options found`));
      }
    });

    proc.on("error", (err) => {
      reject(err);
    });
  });
}

export function clearSessions() {
  for (const session of sessions.values()) {
    session.proc.kill();
  }
  sessions.clear();
}

async function completeImport(selection: string): Promise<string> {
  const sessionEntry = [...sessions.entries()].find(([_, s]) =>
    s.options.includes(selection)
  );

  if (!sessionEntry) {
    throw new Error("Invalid or expired selection");
  }

  const [sessionId, session] = sessionEntry;

  session.proc.stdin.write(selection + "\n");

  return new Promise((resolve, reject) => {
    const onData = (chunk: Buffer) => {
      const text = chunk.toString();
      const match = text.match(/Imported.*?\s+to\s+(\/.*\.tsx)/);

      if (match) {
        session.proc.stdout.off("data", onData);
        session.proc.kill();
        sessions.delete(sessionId);
        resolve(match[1]);
      }
    };

    session.proc.stdout.on("data", onData);

    session.proc.on("exit", (code) => {
      sessions.delete(sessionId);
      reject(new Error(`completeImport: tsci exited with code ${code} without confirming import`));
    });

    session.proc.on("error", (err) => {
      sessions.delete(sessionId);
      reject(err);
    });
  });
}

export async function resolveComponent(
  query: string,
  depth: "surface" | "deep"
): Promise<ResolveResult> {

  const local = await resolveLocal(query);
  if (local) {
    return {
      status: "resolved",
      component: path.basename(local, ".tsx"),
      path: local,
    };
  }

  // is this a selection?
  for (const [sessionId, s] of sessions.entries()) {
    if (s.options.includes(query)) {
      try {
        const importedPath = await completeImport(query);
        console.log("Imported:", importedPath);
        return {
          status: "resolved",
          component: query,
          path: importedPath,
        };
      } catch (err) {
        return {
          status: "error",
          message: err instanceof Error ? err.message : "Import failed",
        };
      }
    }
  }

  try {
    const { sessionId, options } = await startImport(query);
    if (sessionId === "no_results") {
      return {
        status: "no_results",
        message: "No results found matching your query.",
      };
    }
    console.log("Returning options...")
    return {
      status: "selection_required",
      options,
    };
  } catch (err) {
    console.log("resolveComponent Error:", err);
    return {
      status: "error",
      message: "No components found or tsci error",
    };
  }
}
