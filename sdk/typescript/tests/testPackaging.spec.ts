import { mkdtempSync, readFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

import Ajv2020 from "ajv/dist/2020";
import { describe, expect, test } from "vitest";

import { loadAppFactory, packageNodeCli } from "../src/index.js";

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

describe("packageNodeCli", () => {
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
    const entryFile = resolve(projectRoot, "examples", "demo-notes", "src", "cli.ts");
    const appFactory = await loadAppFactory(
      `${resolve(projectRoot, "examples", "demo-notes", "src", "app.ts")}:createApp`
    );
    const outDir = mkdtempSync(resolve(tmpdir(), "aclip-ts-build-"));

    const artifact = await packageNodeCli({
      app: appFactory(),
      executableName: "aclip-demo-notes",
      packageName: "@aclip/demo-notes",
      packageVersion: "0.1.0",
      entryFile,
      projectRoot,
      outDir
    });

    expect(dirname(artifact.entryPath)).toBe(outDir);
    expect(artifact.manifest.distribution).toEqual([
      {
        kind: "npm_package",
        package: "@aclip/demo-notes",
        version: "0.1.0",
        executable: "aclip-demo-notes"
      }
    ]);
    validateAgainstManifestSchema(artifact.manifest);
  });
});
