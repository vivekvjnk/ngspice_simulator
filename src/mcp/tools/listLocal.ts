import fs from "fs/promises";
import path from "path";
import { LOCAL_LIBRARY_DIR } from "../../config/paths.js";
import { getFilesRecursive } from "../../runtime/libraryFs.js";

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
    const allFiles = await getFilesRecursive(LOCAL_LIBRARY_DIR);

    return allFiles
      .filter(f => f.endsWith(".tsx"))
      .map(f => {
        const relativePath = path.relative(LOCAL_LIBRARY_DIR, f);
        return {
          name: relativePath.replace(/\.tsx$/, ""),
          file: relativePath,
        };
      })
      .sort((a, b) => a.name.localeCompare(b.name));
  } catch {
    // Library directory may not exist yet
    return [];
  }
}
