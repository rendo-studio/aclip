import { mkdtempSync, readFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

import Ajv2020 from "ajv/dist/2020";
import { describe, expect, test } from "vitest";

import { AclipApp, build, build_cli, loadAppFactory } from "../src/index.js";

function currentDir() {
  return fileURLToPath(new URL(".", import.meta.url));
}

function validateAgainstManifestSchema(manifest: unknown) {
  const ajv = new Ajv2020({ strict: false });
  const schemaPath = resolve(currentDir(), "..", "..", "..", "schema", "manifest.schema.json");
  const schema = JSON.parse(readFileSync(schemaPath, "utf8"));
  const valid = ajv.validate(schema, manifest);
  expect(valid, JSON.stringify(ajv.errors, null, 2)).toBe(true);
}

describe("build_cli", () => {
  test("loads an app factory from a TypeScript module path", async () => {
    const appFactoryPath = resolve(
      currentDir(),
      "..",
      "examples",
      "demo-notes",
      "src",
      "app.ts"
    );

    const factory = await loadAppFactory(`${appFactoryPath}:createApp`);
    const app = factory();

    expect(app.buildHelpPayload()).toMatchObject({
      type: "help_index",
      protocol: "aclip/0.1"
    });
  });

  test("bundles a node CLI artifact and writes npm distribution metadata", async () => {
    const projectRoot = resolve(currentDir(), "..");
    const outDir = mkdtempSync(resolve(tmpdir(), "aclip-ts-build-"));

    const artifact = await build(`${resolve(projectRoot, "examples", "demo-notes", "src", "app.ts")}:app`, {
      projectRoot,
      outDir
    });

    expect(dirname(artifact.entryPath)).toBe(outDir);
    expect(artifact.manifest.distribution).toEqual([
      {
        kind: "npm_package",
        package: "@rendo-studio/aclip",
        version: "0.2.3",
        executable: "aclip-demo-notes"
      }
    ]);
    validateAgainstManifestSchema(artifact.manifest);
  });

  test("package metadata does not expose a build_cli bin", () => {
    const packageJsonPath = resolve(currentDir(), "..", "package.json");
    const packageJson = JSON.parse(readFileSync(packageJsonPath, "utf8")) as {
      bin?: unknown;
    };

    expect(packageJson.bin).toBeUndefined();
  });

  test("SDK exposes build_cli only as a module-level API", () => {
    const app = new AclipApp({
      name: "notes",
      version: "0.2.3",
      summary: "A minimal notes CLI.",
      description: "Create and inspect notes."
    });

    expect("build_cli" in app).toBe(false);
  });

  test("exports build as an alias of build_cli", () => {
    expect(build).toBe(build_cli);
  });
});
