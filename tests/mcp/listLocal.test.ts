import fs from "fs/promises";
import path from "path";
import { listLocalComponents } from "../../src/mcp/tools/listLocal.js";
import { LOCAL_LIBRARY_DIR } from "../../src/config/paths.js";

describe("listLocalComponents", () => {
  afterEach(async () => {
    try {
      const files = await fs.readdir(LOCAL_LIBRARY_DIR);
      await Promise.all(
        files.map((f: string) =>
          fs.unlink(path.join(LOCAL_LIBRARY_DIR, f))
        )
      );
    } catch {}
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
    expect(result.map(r => r.name)).toEqual(["A", "B"]);
  });
});
