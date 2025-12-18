import fs from "fs/promises";
import path from "path";
import {
  LOCAL_LIBRARY_DIR,
} from "../../config/paths.js";

export type SearchMode = "fuzzy" | "regex";
export type SearchDepth = "surface" | "deep";

export interface SurfaceSearchResult {
  name: string;
  source: "local" | "global";
  description?: string;
}

export interface DeepSearchResult extends SurfaceSearchResult {
  exports?: string[];
  pins?: string[];
}

function searchGlobalLibraryStub(
  query: string,
  mode: SearchMode,
  depth: SearchDepth
): (SurfaceSearchResult | DeepSearchResult)[] {
  const globals = [
    { name: "Resistor", description: "Generic resistor component" },
    { name: "Capacitor", description: "Generic capacitor component" },
    { name: "OpAmp", description: "Generic operational amplifier" },
  ];

  const matcher =
    mode === "regex"
      ? new RegExp(query, "i")
      : null;

  return globals
    .filter(c =>
      mode === "regex"
        ? matcher!.test(c.name)
        : c.name.toLowerCase().includes(query.toLowerCase())
    )
    .map(c =>
      depth === "deep"
        ? {
            name: c.name,
            source: "global",
            description: c.description,
            exports: ["default"],
          }
        : {
            name: c.name,
            source: "global",
            description: c.description,
          }
    );
}

/**
 * Search local and global libraries.
 */
export async function searchLibrary(
  query: string,
  mode: SearchMode,
  depth: SearchDepth
): Promise<(SurfaceSearchResult | DeepSearchResult)[]> {
  let localResults: (SurfaceSearchResult | DeepSearchResult)[] = [];

  try {
    const files = await fs.readdir(LOCAL_LIBRARY_DIR);

    const matcher =
      mode === "regex"
        ? new RegExp(query, "i")
        : null;

    localResults = files
      .filter(f => f.endsWith(".tsx"))
      .map(f => path.basename(f, ".tsx"))
      .filter(name =>
        mode === "regex"
          ? matcher!.test(name)
          : name.toLowerCase().includes(query.toLowerCase())
      )
      .map(name =>
        depth === "deep"
          ? {
              name,
              source: "local",
              exports: ["default"], // best-effort stub
            }
          : {
              name,
              source: "local",
            }
      );
  } catch {
    // ignore missing local library
  }

  const globalResults = searchGlobalLibraryStub(
    query,
    mode,
    depth
  );

  return [
    ...localResults.sort((a, b) =>
      a.name.localeCompare(b.name)
    ),
    ...globalResults.sort((a, b) =>
      a.name.localeCompare(b.name)
    ),
  ];
}
