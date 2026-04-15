import { mkdtempSync, readFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, resolve } from "node:path";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";

import Ajv2020 from "ajv/dist/2020";
import { describe, expect, test } from "vitest";

import { AclipApp, build_cli, loadAppFactory } from "../src/index.js";

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
    const entryFile = resolve(projectRoot, "examples", "demo-notes", "src", "cli.ts");
    const appFactory = await loadAppFactory(
      `${resolve(projectRoot, "examples", "demo-notes", "src", "app.ts")}:createApp`
    );
    const outDir = mkdtempSync(resolve(tmpdir(), "aclip-ts-build-"));

    const artifact = await build_cli({
      app: appFactory(),
      entryFile,
      projectRoot,
      outDir
    });

    expect(dirname(artifact.entryPath)).toBe(outDir);
    expect(artifact.manifest.distribution).toEqual([
      {
        kind: "npm_package",
        package: "@rendo-studio/aclip",
        version: "0.1.2",
        executable: "aclip-demo-notes"
      }
    ]);
    validateAgainstManifestSchema(artifact.manifest);
  });

  test("supports app-centric build_cli on the app instance", async () => {
    const app = new AclipApp({
      name: "demo-cli",
      version: "0.1.0",
      summary: "Demo CLI",
      description: "Demo CLI."
    });

    app.command("version", {
      summary: "Show version",
      description: "Show version.",
      examples: ["demo-cli version"],
      handler: () => ({ version: "0.1.0" })
    });

    const outDir = mkdtempSync(resolve(tmpdir(), "aclip-ts-app-build-"));
    const artifact = await app.build_cli({
      entryFile: resolve(currentDir(), "..", "examples", "demo-notes", "src", "cli.ts"),
      projectRoot: resolve(currentDir(), ".."),
      outDir
    });

    expect(artifact.manifest.name).toBe("demo-cli");
    expect(artifact.manifest.distribution).toEqual([
      {
        kind: "npm_package",
        package: "@rendo-studio/aclip",
        version: "0.1.2",
        executable: "demo-cli"
      }
    ]);
  });

  test("exposes a build_cli CLI entrypoint", () => {
    const projectRoot = resolve(currentDir(), "..");
    const result = spawnSync(
      process.execPath,
      ["--import", "tsx", resolve(projectRoot, "src", "buildCliCli.ts"), "--help"],
      {
        cwd: projectRoot,
        encoding: "utf8"
      }
    );

    expect(result.status).toBe(0);
    expect(result.stdout).toContain("aclip-build-cli");
    expect(result.stdout).toContain("--app-factory");
  });

  test("build_cli CLI wrapper resolves project-relative inputs", () => {
    const projectRoot = resolve(currentDir(), "..");
    const outDir = mkdtempSync(resolve(tmpdir(), "aclip-ts-cli-build-"));
    const result = spawnSync(
      process.execPath,
      [
        "--import",
        "tsx",
        resolve(projectRoot, "src", "buildCliCli.ts"),
        "--app-factory",
        "./examples/demo-notes/src/app.ts:createApp",
        "--entry-file",
        "./examples/demo-notes/src/cli.ts",
        "--project-root",
        ".",
        "--out-dir",
        outDir
      ],
      {
        cwd: projectRoot,
        encoding: "utf8"
      }
    );

    expect(result.status).toBe(0);
    expect(result.stdout).toContain(`${outDir}\\aclip-demo-notes.cjs`);
    expect(result.stdout).toContain(`${outDir}\\aclip-demo-notes.aclip.json`);
  });
});
