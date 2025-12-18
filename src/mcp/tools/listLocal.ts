import fs from "fs/promises";
import path from "path";
import { LOCAL_LIBRARY_DIR } from "../../config/paths.js";

export interface LocalComponentSummary {
  name: string;
  file: string;
}

/**
 * List components explicitly added to the local library.
 * Read-only. Deterministic.
 */
export async function listLocalComponents(): Promise<
  LocalComponentSummary[]
> {
  try {
    const entries = await fs.readdir(LOCAL_LIBRARY_DIR);

    return entries
      .filter(f => f.endsWith(".tsx"))
      .map(f => ({
        name: path.basename(f, ".tsx"),
        file: f,
      }))
      .sort((a, b) => a.name.localeCompare(b.name));
  } catch {
    // Library directory may not exist yet
    return [];
  }
}
