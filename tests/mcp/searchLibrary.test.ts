import fs from "fs/promises";
import path from "path";
import { searchLibrary } from "../../src/mcp/tools/searchLibrary.js";
import { LOCAL_LIBRARY_DIR } from "../../src/config/paths.js";

describe("searchLibrary", () => {
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

  test("finds local and global components (fuzzy, surface)", async () => {
    await fs.writeFile(
      path.join(LOCAL_LIBRARY_DIR, "ISO7342.tsx"),
      "export const ISO7342 = () => null;"
    );

    const result = await searchLibrary(
      "iso",
      "fuzzy",
      "surface"
    );

    const names = result.map(r => r.name);
    expect(names).toContain("ISO7342");
    
  });
  test("finds global components when query matches global stub", async () => {
    const result = await searchLibrary(
        "res",
        "fuzzy",
        "surface"
    );

    const names = result.map(r => r.name);
    expect(names).toContain("Resistor");
    });

  test("supports regex search", async () => {
    const result = await searchLibrary(
      "^Op",
      "regex",
      "surface"
    );

    expect(result.some(r => r.name === "OpAmp")).toBe(true);
  });

  test("deep search includes exports field", async () => {
    const result = await searchLibrary(
      "res",
      "fuzzy",
      "deep"
    );

    expect(
      result.some(
        r => "exports" in r && Array.isArray((r as any).exports)
      )
    ).toBe(true);
  });
});
