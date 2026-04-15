import { mkdtempSync } from "node:fs";
import { tmpdir } from "node:os";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { spawnSync } from "node:child_process";

import { describe, expect, test } from "vitest";

import { build_cli, loadAppFactory } from "../src/index.js";

function currentDir() {
  return fileURLToPath(new URL(".", import.meta.url));
}

describe("demo notes CLI", () => {
  test("prints canonical markdown help from the bundled node artifact", async () => {
    const projectRoot = resolve(currentDir(), "..");
    const outDir = mkdtempSync(resolve(tmpdir(), "aclip-ts-demo-"));
    const entryFile = resolve(projectRoot, "examples", "demo-notes", "src", "cli.ts");
    const appFactory = await loadAppFactory(
      `${resolve(projectRoot, "examples", "demo-notes", "src", "app.ts")}:createApp`
    );

    const artifact = await build_cli({
      app: appFactory(),
      executableName: "aclip-demo-notes",
      packageName: "@aclip/demo-notes",
      packageVersion: "0.1.0",
      entryFile,
      projectRoot,
      outDir
    });

    const result = spawnSync(process.execPath, [artifact.entryPath, "--help"], {
      encoding: "utf8",
      env: {
        ...process.env,
        NODE_OPTIONS: ""
      }
    });

    expect(result.status).toBe(0);
    expect(result.stdout).toContain("# aclip-demo-notes");
    expect(result.stdout).toContain("## Command Groups");
    expect(result.stdout).toContain("Next: run `aclip-demo-notes <path> --help`");
  });

  test("executes bundled commands and emits result envelopes", async () => {
    const projectRoot = resolve(currentDir(), "..");
    const outDir = mkdtempSync(resolve(tmpdir(), "aclip-ts-demo-"));
    const entryFile = resolve(projectRoot, "examples", "demo-notes", "src", "cli.ts");
    const storePath = resolve(outDir, "notes.json");
    const appFactory = await loadAppFactory(
      `${resolve(projectRoot, "examples", "demo-notes", "src", "app.ts")}:createApp`
    );

    const artifact = await build_cli({
      app: appFactory(),
      executableName: "aclip-demo-notes",
      packageName: "@aclip/demo-notes",
      packageVersion: "0.1.0",
      entryFile,
      projectRoot,
      outDir
    });

    const result = spawnSync(
      process.execPath,
      [
        artifact.entryPath,
        "note",
        "create",
        "--title",
        "hello",
        "--body",
        "world",
        "--store",
        storePath
      ],
      {
        encoding: "utf8",
        env: {
          ...process.env,
          NODE_OPTIONS: ""
        }
      }
    );

    expect(result.status).toBe(0);
    expect(JSON.parse(result.stdout)).toMatchObject({
      protocol: "aclip/0.1",
      type: "result",
      ok: true,
      command: "note create"
    });
  });
});
