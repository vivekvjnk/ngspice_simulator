import fs from "fs/promises";
import path from "path";
import ts from "typescript";

export interface ValidationResult {
  success: boolean;
  errors: string[];
}

export async function validateComponent(
  tempFilePath: string
): Promise<ValidationResult> {
  const errors: string[] = [];

  // ---------- Layer 1: file existence ----------
  let sourceText: string;
  try {
    sourceText = await fs.readFile(tempFilePath, "utf-8");
  } catch {
    return {
      success: false,
      errors: ["Temp component file does not exist"],
    };
  }

  if (path.extname(tempFilePath) !== ".tsx") {
    return {
      success: false,
      errors: ["Component file must have .tsx extension"],
    };
  }

  // ---------- Layer 2: Create Program ----------
  const compilerOptions: ts.CompilerOptions = {
    target: ts.ScriptTarget.ES2022,
    module: ts.ModuleKind.ESNext,
    jsx: ts.JsxEmit.ReactJSX,
    strict: true,
    noEmit: true,
  };

  const host = ts.createCompilerHost(compilerOptions);

  // Override file reading to control inputs
  host.readFile = (fileName: string) =>
    fileName === tempFilePath ? sourceText : undefined;

  host.fileExists = (fileName: string) =>
    fileName === tempFilePath;

  const program = ts.createProgram(
    [tempFilePath],
    compilerOptions,
    host
  );

  const sourceFile = program.getSourceFile(tempFilePath);
  if (!sourceFile) {
    return {
      success: false,
      errors: ["Failed to load source file into program"],
    };
  }

  // ---------- Layer 3: Diagnostics ----------
  const diagnostics = [
    ...program.getSyntacticDiagnostics(sourceFile),
    ...program.getSemanticDiagnostics(sourceFile),
  ];

  if (diagnostics.length > 0) {
    diagnostics.forEach((d: ts.Diagnostic) => {
      errors.push(
        ts.flattenDiagnosticMessageText(
          d.messageText,
          "\n"
        )
      );
    });

    return { success: false, errors };
  }

  // ---------- Layer 4: Export detection ----------
  let hasExport = false;

  sourceFile.forEachChild(node => {
    // export default ...
    if (ts.isExportAssignment(node)) {
      hasExport = true;
    }

    // export const / function / class / etc
    if (
      ts.canHaveModifiers(node) &&
      node.modifiers?.some(
        m => m.kind === ts.SyntaxKind.ExportKeyword
      )
    ) {
      hasExport = true;
    }
  });

  if (!hasExport) {
    return {
      success: false,
      errors: ["Component must export at least one symbol"],
    };
  }

  return {
    success: true,
    errors: [],
  };
}
