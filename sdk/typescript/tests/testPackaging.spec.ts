import { mkdtempSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

import Ajv2020 from "ajv/dist/2020";
import { describe, expect, test } from "vitest";

import {
  AclipApp,
  build,
  build_cli,
  credentialToManifest,
  envCredential,
  export_skills,
  fileCredential,
  loadAppFactory,
  loadAppTarget
} from "../src/index.js";

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

function writeSkillSource(
  root: string,
  options: {
    name: string;
    description: string;
    metadata?: Record<string, string>;
  }
): string {
  const skillDir = resolve(root, options.name);
  mkdirSync(skillDir, { recursive: true });
  const metadataLines = options.metadata
    ? `metadata:\n${Object.entries(options.metadata)
        .map(([key, value]) => `  ${key}: ${value}`)
        .join("\n")}\n`
    : "";
  writeFileSync(
    resolve(skillDir, "SKILL.md"),
    [
      "---",
      `name: ${options.name}`,
      `description: ${options.description}`,
      metadataLines.trimEnd(),
      "---",
      "",
      `# ${options.name}`,
      "",
      "Developer-authored skill body.",
      ""
    ]
      .filter((line) => line !== "")
      .join("\n"),
    "utf8"
  );
  mkdirSync(resolve(skillDir, "references"), { recursive: true });
  writeFileSync(resolve(skillDir, "references", "README.md"), "reference", "utf8");
  return skillDir;
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
    const projectRoot = resolve(currentDir(), "..", "examples", "demo-notes");
    const outDir = mkdtempSync(resolve(tmpdir(), "aclip-ts-build-"));

    const artifact = await build(`${resolve(projectRoot, "src", "app.ts")}:app`, {
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
  }, 20000);

  test("requires an explicit packageVersion when package.json.version diverges from AclipApp.version", async () => {
    const projectRoot = resolve(currentDir(), "..");
    const outDir = mkdtempSync(resolve(tmpdir(), "aclip-ts-build-mismatch-"));

    await expect(
      build(`${resolve(projectRoot, "examples", "demo-notes", "src", "app.ts")}:app`, {
        projectRoot,
        outDir
      })
    ).rejects.toThrow("package.json version does not match AclipApp.version");
  });

  test("preserves explicit packageName overrides", async () => {
    const projectRoot = resolve(currentDir(), "..", "examples", "demo-notes");
    const outDir = mkdtempSync(resolve(tmpdir(), "aclip-ts-build-package-name-"));

    const artifact = await build(`${resolve(projectRoot, "src", "app.ts")}:app`, {
      projectRoot,
      outDir,
      packageName: "@custom/demo-notes"
    });

    expect(artifact.manifest.distribution).toEqual([
      {
        kind: "npm_package",
        package: "@custom/demo-notes",
        version: "0.1.0",
        executable: "aclip-demo-notes"
      }
    ]);
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
      version: "0.2.4",
      summary: "A minimal notes CLI.",
      description: "Create and inspect notes."
    });

    expect("build_cli" in app).toBe(false);
  });

  test("exports build as an alias of build_cli", () => {
    expect(build).toBe(build_cli);
  });

  test("credential manifests support env and file sources", () => {
    expect(
      credentialToManifest(
        envCredential("notes_token", {
          envVar: "ACLIP_NOTES_TOKEN",
          description: "Token for remote notes access.",
          required: true
        })
      )
    ).toEqual({
      name: "notes_token",
      source: "env",
      envVar: "ACLIP_NOTES_TOKEN",
      description: "Token for remote notes access.",
      required: true
    });

    expect(
      credentialToManifest(
        fileCredential("notes_token_file", {
          path: ".secrets/notes-token.txt",
          description: "Path to a local token file."
        })
      )
    ).toEqual({
      name: "notes_token_file",
      source: "file",
      path: ".secrets/notes-token.txt",
      description: "Path to a local token file.",
      required: false
    });
  });

  test("export_skills copies CLI and command skill packages with ACLIP anchors", async () => {
    const app = await loadAppTarget(`${resolve(currentDir(), "..", "examples", "demo-notes", "src", "app.ts")}:app`);
    const skillsRoot = mkdtempSync(resolve(tmpdir(), "aclip-ts-skills-src-"));
    const outDir = mkdtempSync(resolve(tmpdir(), "aclip-ts-skills-dist-"));

    const cliSkillDir = writeSkillSource(skillsRoot, {
      name: "notes-overview",
      description: "Use the notes CLI safely.",
      metadata: { author: "demo" }
    });
    const commandSkillDir = writeSkillSource(skillsRoot, {
      name: "note-create-best-practice",
      description: "Create notes with the recommended flow."
    });

    app.addCliSkill(cliSkillDir);
    app.addCommandSkill(["note", "create"], commandSkillDir, {
      metadata: { custom: "true" }
    });

    const artifact = await export_skills(app, { outDir });

    expect(artifact.indexPath).toBe(resolve(outDir, "skills.aclip.json"));
    expect(artifact.index.packages.map((entry) => entry.kind)).toEqual(["cli", "command"]);
    expect(readFileSync(resolve(outDir, "notes-overview", "references", "README.md"), "utf8")).toBe("reference");

    const cliText = readFileSync(resolve(outDir, "notes-overview", "SKILL.md"), "utf8");
    expect(cliText).toContain("aclip-cli-name: aclip-demo-notes");
    expect(cliText).toContain("aclip-hook-kind: cli");
    expect(cliText).toContain("author: demo");

    const commandText = readFileSync(resolve(outDir, "note-create-best-practice", "SKILL.md"), "utf8");
    expect(commandText).toContain("aclip-hook-kind: command");
    expect(commandText).toContain("aclip-command-path: note create");
    expect(commandText).toContain("aclip-command-summary: Create a note");
    expect(commandText).toContain("custom: true");
  });

  test("export_skills rejects packages without SKILL.md", async () => {
    const app = new AclipApp({
      name: "notes",
      version: "0.3.2",
      summary: "A minimal notes CLI.",
      description: "Create and inspect notes."
    });
    const brokenSkillDir = mkdtempSync(resolve(tmpdir(), "aclip-ts-broken-skill-"));
    const outDir = mkdtempSync(resolve(tmpdir(), "aclip-ts-broken-skill-out-"));

    app.addCliSkill(brokenSkillDir);

    await expect(export_skills(app, { outDir })).rejects.toThrow(/SKILL\.md/);
  });
});
