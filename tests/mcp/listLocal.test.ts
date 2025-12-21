import fs from "fs/promises";
import { jest } from "@jest/globals";
import path from "path";

// Create a unique ID for this test suite run
const TEST_ID = "listLocal_" + Math.random().toString(36).substring(7);
const TEST_ROOT = path.join(process.cwd(), ".test_env", TEST_ID);
const LOCAL_LIBRARY_DIR = path.join(TEST_ROOT, "library", "local");

// Set environment variable for isolation BEFORE importing the module
process.env.VHL_LIBRARY_DIR = LOCAL_LIBRARY_DIR;

describe("listLocalComponents", () => {
  let listLocalComponents: any;

  beforeAll(async () => {
    // Create the isolated directory
    await fs.mkdir(LOCAL_LIBRARY_DIR, { recursive: true });

    // Dynamically import the tool to ensure it picks up the environment variable
    // This bypasses potential hoisting issues with static imports
    const module = await import("../../src/mcp/tools/listLocal.js");
    listLocalComponents = module.listLocalComponents;
  });

  afterEach(async () => {
    try {
      const files = await fs.readdir(LOCAL_LIBRARY_DIR);
      await Promise.all(
        files.map((f: string) =>
          fs.unlink(path.join(LOCAL_LIBRARY_DIR, f))
        )
      );
    } catch { }
  });

  afterAll(async () => {
    // Cleanup the test environment
    try {
      await fs.rm(TEST_ROOT, { recursive: true, force: true });
    } catch { }
  });

  test("returns empty array when library is empty", async () => {
    const result = await listLocalComponents();
    expect(result).toEqual([]);
  });

  test("lists local components deterministically", async () => {
    await fs.writeFile(
      path.join(LOCAL_LIBRARY_DIR, "B.tsx"),
      "export const B = () => null;"
    );
    await fs.writeFile(
      path.join(LOCAL_LIBRARY_DIR, "A.tsx"),
      "export const A = () => null;"
    );

    const result = await listLocalComponents();
    expect(result.map((r: any) => r.name)).toEqual(["A", "B"]);
  });
});
