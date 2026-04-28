import { mkdtempSync } from "node:fs";
import { tmpdir } from "node:os";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { spawnSync } from "node:child_process";

import { describe, expect, test } from "vitest";

import { build_cli } from "../src/index.js";

function currentDir() {
  return fileURLToPath(new URL(".", import.meta.url));
}

describe("demo notes CLI", () => {
  test("prints canonical markdown help from the bundled node artifact", async () => {
    const projectRoot = resolve(currentDir(), "..", "examples", "demo-notes");
    const outDir = mkdtempSync(resolve(tmpdir(), "aclip-ts-demo-"));
    const artifact = await build_cli({
      factory: `${resolve(projectRoot, "src", "app.ts")}:createApp`,
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
  }, 20000);

  test("supports help alias and subtree --all expansion", async () => {
    const projectRoot = resolve(currentDir(), "..", "examples", "demo-notes");
    const outDir = mkdtempSync(resolve(tmpdir(), "aclip-ts-demo-"));
    const artifact = await build_cli({
      factory: `${resolve(projectRoot, "src", "app.ts")}:createApp`,
      projectRoot,
      outDir
    });

    const helpAlias = spawnSync(process.execPath, [artifact.entryPath, "help"], {
      encoding: "utf8",
      env: {
        ...process.env,
        NODE_OPTIONS: ""
      }
    });
    const helpAll = spawnSync(process.execPath, [artifact.entryPath, "note", "--help", "--all"], {
      encoding: "utf8",
      env: {
        ...process.env,
        NODE_OPTIONS: ""
      }
    });

    expect(helpAlias.status).toBe(0);
    expect(helpAlias.stdout).toContain("# aclip-demo-notes");
    expect(helpAll.status).toBe(0);
    expect(helpAll.stdout).toContain("\n---\n\n# note create\n\n");
    expect(helpAll.stdout).toContain("\n---\n\n# note list\n\n");
  }, 20000);

  test("prints the configured root version from the bundled node artifact", async () => {
    const projectRoot = resolve(currentDir(), "..", "examples", "demo-notes");
    const outDir = mkdtempSync(resolve(tmpdir(), "aclip-ts-demo-"));
    const artifact = await build_cli({
      factory: `${resolve(projectRoot, "src", "app.ts")}:createApp`,
      projectRoot,
      outDir
    });

    const result = spawnSync(process.execPath, [artifact.entryPath, "--version"], {
      encoding: "utf8",
      env: {
        ...process.env,
        NODE_OPTIONS: ""
      }
    });

    expect(result.status).toBe(0);
    expect(result.stdout).toBe("aclip-demo-notes 0.1.0\n");

    const shortResult = spawnSync(process.execPath, [artifact.entryPath, "-V"], {
      encoding: "utf8",
      env: {
        ...process.env,
        NODE_OPTIONS: ""
      }
    });
    const lowerShortResult = spawnSync(process.execPath, [artifact.entryPath, "-v"], {
      encoding: "utf8",
      env: {
        ...process.env,
        NODE_OPTIONS: ""
      }
    });

    expect(shortResult.status).toBe(0);
    expect(shortResult.stdout).toBe("aclip-demo-notes 0.1.0\n");
    expect(lowerShortResult.status).toBe(0);
    expect(lowerShortResult.stdout).toBe("aclip-demo-notes 0.1.0\n");
  }, 20000);

  test("omits repeated next-step guidance on group help and avoids repeated command summary lines", async () => {
    const projectRoot = resolve(currentDir(), "..", "examples", "demo-notes");
    const outDir = mkdtempSync(resolve(tmpdir(), "aclip-ts-demo-"));
    const artifact = await build_cli({
      factory: `${resolve(projectRoot, "src", "app.ts")}:createApp`,
      projectRoot,
      outDir
    });

    const groupHelp = spawnSync(process.execPath, [artifact.entryPath, "note", "--help"], {
      encoding: "utf8",
      env: {
        ...process.env,
        NODE_OPTIONS: ""
      }
    });
    const commandHelp = spawnSync(process.execPath, [artifact.entryPath, "note", "create", "--help"], {
      encoding: "utf8",
      env: {
        ...process.env,
        NODE_OPTIONS: ""
      }
    });

    expect(groupHelp.status).toBe(0);
    expect(groupHelp.stdout).not.toContain("Next: run `aclip-demo-notes <path> --help`");
    expect(commandHelp.status).toBe(0);
    expect(commandHelp.stdout).toContain("# note create\n\nCreate a note in a local JSON store.\n\n## Usage");
    expect(commandHelp.stdout).not.toContain("# note create\n\nCreate a note\n\nCreate a note in a local JSON store.");
  }, 20000);

  test("executes bundled commands and preserves app-defined success output", async () => {
    const projectRoot = resolve(currentDir(), "..", "examples", "demo-notes");
    const outDir = mkdtempSync(resolve(tmpdir(), "aclip-ts-demo-"));
    const storePath = resolve(outDir, "notes.json");
    const artifact = await build_cli({
      factory: `${resolve(projectRoot, "src", "app.ts")}:createApp`,
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
      note: {
        title: "hello",
        body: "world"
      },
      store: storePath
    });
  }, 20000);
});
