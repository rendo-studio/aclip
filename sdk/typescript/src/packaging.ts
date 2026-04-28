import { spawnSync } from "node:child_process";
import { randomUUID } from "node:crypto";
import { chmodSync, cpSync, existsSync, mkdirSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { createRequire } from "node:module";
import { basename, dirname, extname, relative, resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

import type { AclipApp } from "./app.js";
import type { CliSkillHook, CommandSkillHook, CommandSpec } from "./contracts.js";

export interface CliArtifact {
  entryPath: string;
  manifestPath: string;
  manifest: Record<string, unknown>;
}

export interface ExportedSkillPackage {
  name: string;
  kind: "cli" | "command";
  sourceDir: string;
  outputDir: string;
  commandPath?: string;
}

export interface SkillExportArtifact {
  outputDir: string;
  indexPath: string;
  index: {
    protocol: "aclip-skill-export/0.1";
    cli: {
      name: string;
      version: string;
    };
    packages: Array<{
      name: string;
      kind: "cli" | "command";
      path: string;
      commandPath?: string;
    }>;
  };
  packages: ExportedSkillPackage[];
}

interface SkillFrontmatter {
  name: string;
  description: string;
  metadata: Record<string, string>;
  compatibility?: string;
  license?: string;
  allowedTools?: string;
  extras?: Record<string, string>;
}

export interface BuildCliOptions {
  factory?: string;
  appFactory?: string;
  projectRoot?: string;
  outDir?: string;
  packageName?: string;
  packageVersion?: string;
}

interface AppFactoryInfo {
  target: string;
  modulePath: string;
  exportName: string;
}

export async function loadAppFactory(target: string): Promise<() => AclipApp> {
  const info = inspectAppFactoryTarget(target);
  const importedModule = await loadFactoryModule(info.modulePath);
  const factory = importedModule[info.exportName];

  if (typeof factory !== "function") {
    throw new Error("app factory target must resolve to a callable export");
  }

  return factory as () => AclipApp;
}

export async function loadAppTarget(target: string): Promise<AclipApp> {
  const info = inspectAppFactoryTarget(target);
  const importedModule = await loadFactoryModule(info.modulePath);
  return resolveImportedAppTarget(importedModule[info.exportName]);
}

type BuildCliOverrides = Omit<BuildCliOptions, "factory" | "appFactory">;

export async function build_cli(target: string, overrides?: BuildCliOverrides): Promise<CliArtifact>;
export async function build_cli(options: BuildCliOptions): Promise<CliArtifact>;
export async function build_cli(
  targetOrOptions: string | BuildCliOptions,
  overrides: BuildCliOverrides = {}
): Promise<CliArtifact> {
  const normalizedOptions = normalizeBuildCliOptions(targetOrOptions, overrides);
  const factoryInfo = inspectAppFactoryTarget(normalizedOptions.factory, normalizedOptions.projectRoot);
  const projectRoot = resolveProjectRoot(factoryInfo.modulePath, normalizedOptions.projectRoot);
  const app = await loadAppTarget(factoryInfo.target);
  const outDir = normalizedOptions.outDir ?? resolve(projectRoot, "dist");
  const tempDir = resolve(projectRoot, ".aclip-build", randomUUID());
  const runtimeImportSpecifier = defaultSdkRuntimeImportSpecifier();
  const launcherFile = writeLauncherFile(tempDir, factoryInfo, runtimeImportSpecifier);
  const launcherEntry = relativeImportPath(projectRoot, launcherFile);
  const packageMetadata = readPackageMetadata(projectRoot);
  const binaryName = app.name;
  const packageName = normalizedOptions.packageName ?? packageMetadata.name;
  if (!packageName) {
    throw new Error("package name is required for build_cli; set packageName or define package.json.name");
  }
  const appVersion = requireAppVersion(app, "building the npm distribution metadata");
  const packageVersion = normalizedOptions.packageVersion ?? appVersion;
  if (
    packageMetadata.version &&
    packageMetadata.version !== packageVersion &&
    normalizedOptions.packageVersion === undefined
  ) {
    throw new Error(
      "package.json version does not match AclipApp.version; align them or set packageVersion explicitly"
    );
  }
  const tsupConfigFile = writeTsupConfigFile(tempDir, {
    binaryName,
    launcherEntry,
    outDir,
    sdkPackageName: defaultSdkPackageName(),
    sdkRuntimeImportSpecifier: runtimeImportSpecifier,
  });

  mkdirSync(outDir, { recursive: true });

  try {
    runTsupBuild({
      projectRoot,
      tsupConfigFile,
    });
  } finally {
    rmSync(tempDir, { recursive: true, force: true });
  }

  const entryPath = resolve(outDir, `${binaryName}.cjs`);
  try {
    chmodSync(entryPath, 0o755);
  } catch {
    // chmod is best-effort on Windows
  }

  const manifest = app.buildIndexManifest({
    distribution: [
      {
        kind: "npm_package",
        package: packageName,
        version: packageVersion,
        executable: binaryName
      }
    ]
  });
  const manifestPath = resolve(outDir, `${binaryName}.aclip.json`);
  writeFileSync(manifestPath, JSON.stringify(manifest, null, 2), "utf8");

  return {
    entryPath,
    manifestPath,
    manifest
  };
}

export async function export_skills(
  app: AclipApp,
  options: { outDir: string }
): Promise<SkillExportArtifact> {
  const outputDir = resolve(options.outDir);
  mkdirSync(outputDir, { recursive: true });
  const appVersion = requireAppVersion(app, "exporting skills");

  const packages: ExportedSkillPackage[] = [];
  const seenNames = new Set<string>();

  for (const hook of app.cliSkills) {
    packages.push(
      exportSkillPackage({
        app,
        hook,
        kind: "cli",
        outputDir,
        seenNames
      })
    );
  }

  for (const hook of app.commandSkills) {
    packages.push(
      exportSkillPackage({
        app,
        hook,
        kind: "command",
        outputDir,
        seenNames
      })
    );
  }

  const index: SkillExportArtifact["index"] = {
    protocol: "aclip-skill-export/0.1",
    cli: {
      name: app.name,
      version: appVersion
    },
    packages: packages.map((entry) => ({
      name: entry.name,
      kind: entry.kind,
      path: basename(entry.outputDir),
      ...(entry.commandPath ? { commandPath: entry.commandPath } : {})
    }))
  };
  const indexPath = resolve(outputDir, "skills.aclip.json");
  writeFileSync(indexPath, JSON.stringify(index, null, 2), "utf8");

  return {
    outputDir,
    indexPath,
    index,
    packages
  };
}

function normalizeBuildCliOptions(
  targetOrOptions: string | BuildCliOptions,
  overrides: BuildCliOverrides
): Required<Pick<BuildCliOptions, "factory">> & BuildCliOptions {
  const options =
    typeof targetOrOptions === "string"
      ? {
          ...overrides,
          factory: targetOrOptions
        }
      : targetOrOptions;
  const factory = options.factory ?? options.appFactory;
  if (!factory) {
    throw new Error("build_cli requires a factory target");
  }

  return {
    ...options,
    factory
  };
}

async function resolveImportedAppTarget(exported: unknown): Promise<AclipApp> {
  const app = typeof exported === "function" ? await exported() : exported;
  if (!isAclipAppLike(app)) {
    throw new Error("app target must resolve to an ACLIP app instance or no-arg factory");
  }
  return app;
}

function isAclipAppLike(value: unknown): value is AclipApp {
  return (
    typeof value === "object" &&
    value !== null &&
    typeof (value as { run?: unknown }).run === "function" &&
    typeof (value as { buildIndexManifest?: unknown }).buildIndexManifest === "function" &&
    typeof (value as { name?: unknown }).name === "string"
  );
}

function inspectAppFactoryTarget(target: string, projectRoot?: string): AppFactoryInfo {
  const separator = target.lastIndexOf(":");
  if (separator <= 0) {
    throw new Error("app factory must use the form '<module-path>:<export-name>'");
  }

  const modulePath = target.slice(0, separator);
  const exportName = target.slice(separator + 1);
  const resolvedModulePath = resolve(
    projectRoot ?? process.cwd(),
    modulePath
  );

  return {
    target: `${resolvedModulePath}:${exportName}`,
    modulePath: resolvedModulePath,
    exportName
  };
}

function resolveProjectRoot(modulePath: string, explicitProjectRoot?: string): string {
  if (explicitProjectRoot) {
    return resolve(explicitProjectRoot);
  }

  let current = dirname(modulePath);
  while (true) {
    if (basename(current) === "src") {
      return dirname(current);
    }
    try {
      readFileSync(resolve(current, "package.json"), "utf8");
      return current;
    } catch {
      const parent = dirname(current);
      if (parent === current) {
        return dirname(modulePath);
      }
      current = parent;
    }
  }
}

function writeLauncherFile(
  tempDir: string,
  factoryInfo: AppFactoryInfo,
  sdkImportSpecifier: string
): string {
  mkdirSync(tempDir, { recursive: true });
  const relativeModulePath = relativeImportPath(tempDir, factoryInfo.modulePath);
  const resolvedSdkImportSpecifier = normalizeImportSpecifier(tempDir, sdkImportSpecifier);
  const importLine =
    factoryInfo.exportName === "default"
      ? `import createApp from ${JSON.stringify(relativeModulePath)};`
      : `import { ${factoryInfo.exportName} as createApp } from ${JSON.stringify(relativeModulePath)};`;

  const launcherPath = resolve(tempDir, "buildCliLauncher.ts");
  writeFileSync(
    launcherPath,
    [
      `import { cliMain } from ${JSON.stringify(resolvedSdkImportSpecifier)};`,
      importLine,
      "",
      "void cliMain(createApp);",
      ""
    ].join("\n"),
    "utf8"
  );
  return launcherPath;
}

function relativeImportPath(fromDir: string, targetPath: string): string {
  const normalized = relative(fromDir, targetPath).replaceAll("\\", "/");
  if (normalized.startsWith("../") || normalized.startsWith("./")) {
    return normalized;
  }
  return `./${normalized}`;
}

function normalizeImportSpecifier(fromDir: string, specifier: string): string {
  if (specifier.startsWith(".") || specifier.startsWith("/") || /^[A-Za-z]:/.test(specifier)) {
    return relativeImportPath(fromDir, resolve(specifier));
  }
  return specifier;
}

function readPackageMetadata(projectRoot: string): { name?: string; version?: string } {
  const packageJsonPath = resolve(projectRoot, "package.json");
  const packageJson = JSON.parse(readFileSync(packageJsonPath, "utf8")) as {
    name?: string;
    version?: string;
  };
  return {
    name: packageJson.name,
    version: packageJson.version
  };
}

function defaultSdkRuntimeImportSpecifier(): string {
  const currentFile = fileURLToPath(import.meta.url);
  const runtimeFile = currentFile.endsWith(".ts") ? "runtimeEntry.ts" : "runtime.js";
  return resolve(dirname(currentFile), runtimeFile);
}

function defaultSdkPackageName(): string {
  const currentFile = fileURLToPath(import.meta.url);
  const packageJson = JSON.parse(
    readFileSync(resolve(dirname(currentFile), "..", "package.json"), "utf8")
  ) as { name?: string };
  if (!packageJson.name) {
    throw new Error("ACLIP package name could not be determined for build_cli");
  }
  return packageJson.name;
}

async function loadFactoryModule(modulePath: string): Promise<Record<string, unknown>> {
  const extension = extname(modulePath);
  if (extension === ".ts" || extension === ".mts" || extension === ".cts") {
    const { tsImport } = await import("tsx/esm/api");
    return (await tsImport(pathToFileURL(modulePath).href, import.meta.url)) as Record<string, unknown>;
  }

  return (await import(pathToFileURL(modulePath).href)) as Record<string, unknown>;
}

function runTsupBuild(options: {
  projectRoot: string;
  tsupConfigFile: string;
}): void {
  const require = createRequire(import.meta.url);
  const tsupCliPath = require.resolve("tsup/dist/cli-default.js");
  const result = spawnSync(
    process.execPath,
    [
      tsupCliPath,
      "--config",
      options.tsupConfigFile,
    ],
    {
      cwd: options.projectRoot,
      encoding: "utf8",
    },
  );

  if (result.status !== 0) {
    throw new Error(
      result.stderr.trim() || result.stdout.trim() || "tsup build failed",
    );
  }
}

function writeTsupConfigFile(
  tempDir: string,
  options: {
    binaryName: string;
    launcherEntry: string;
    outDir: string;
    sdkPackageName: string;
    sdkRuntimeImportSpecifier: string;
  },
): string {
  const configPath = resolve(tempDir, "tsup.build.config.ts");
  writeFileSync(
    configPath,
    [
      'import { defineConfig } from "tsup";',
      "",
      "export default defineConfig({",
      `  entry: { ${JSON.stringify(options.binaryName)}: ${JSON.stringify(options.launcherEntry)} },`,
      `  outDir: ${JSON.stringify(options.outDir)},`,
      '  format: ["cjs"],',
      '  platform: "node",',
      '  target: "node22",',
      "  clean: true,",
      "  dts: false,",
      "  sourcemap: false,",
      "  silent: true,",
      "  splitting: false,",
      `  noExternal: [${JSON.stringify(options.sdkPackageName)}, "commander"],`,
      "  esbuildOptions(buildOptions) {",
      "    buildOptions.alias = {",
      "      ...(buildOptions.alias ?? {}),",
      `      ${JSON.stringify(options.sdkPackageName)}: ${JSON.stringify(options.sdkRuntimeImportSpecifier)},`,
      "    };",
      "  },",
      '  banner: { js: "#!/usr/bin/env node" },',
      "});",
      "",
    ].join("\n"),
    "utf8",
  );
  return configPath;
}

export const build = build_cli;

function exportSkillPackage(options: {
  app: AclipApp;
  hook: CliSkillHook | CommandSkillHook;
  kind: "cli" | "command";
  outputDir: string;
  seenNames: Set<string>;
}): ExportedSkillPackage {
  const sourceDir = resolve(options.hook.sourceDir);
  const skillMarkdownPath = resolve(sourceDir, "SKILL.md");
  if (!existsSync(skillMarkdownPath)) {
    throw new Error(`skill package must contain SKILL.md: ${sourceDir}`);
  }

  const { frontmatter, body } = parseSkillMarkdown(readFileSync(skillMarkdownPath, "utf8"));
  validateSkillFrontmatter(frontmatter);

  if (options.seenNames.has(frontmatter.name)) {
    throw new Error(`duplicate exported skill package name: ${frontmatter.name}`);
  }
  options.seenNames.add(frontmatter.name);

  const generatedMetadata: Record<string, string> = {
    "aclip-hook-kind": options.kind,
    "aclip-cli-name": options.app.name,
    "aclip-cli-version": requireAppVersion(options.app, "exporting skills")
  };
  let commandPath: string | undefined;

  if (hasGroup(options.app, "auth")) {
    generatedMetadata["aclip-auth-group"] = "auth";
  }
  if (hasGroup(options.app, "doctor")) {
    generatedMetadata["aclip-doctor-group"] = "doctor";
  }

  if (options.kind === "command") {
    const commandHook = options.hook as CommandSkillHook;
    const command = findCommand(options.app, commandHook.commandPath);
    commandPath = command.path.join(" ");
    generatedMetadata["aclip-command-path"] = commandPath;
    generatedMetadata["aclip-command-summary"] = command.summary;
    generatedMetadata["aclip-command-description"] = command.description;
  }

  const exportedFrontmatter: SkillFrontmatter = {
    name: frontmatter.name,
    description: frontmatter.description,
    license: frontmatter.license,
    compatibility: frontmatter.compatibility,
    allowedTools: frontmatter.allowedTools,
    extras: { ...(frontmatter.extras ?? {}) },
    metadata: {
      ...frontmatter.metadata,
      ...((options.hook.metadata ?? {}) as Record<string, string>),
      ...generatedMetadata
    }
  };

  const destinationDir = resolve(options.outputDir, frontmatter.name);
  rmSync(destinationDir, { recursive: true, force: true });
  cpSync(sourceDir, destinationDir, { recursive: true });
  writeFileSync(
    resolve(destinationDir, "SKILL.md"),
    renderSkillMarkdown(exportedFrontmatter, body),
    "utf8"
  );

  return {
    name: frontmatter.name,
    kind: options.kind,
    sourceDir,
    outputDir: destinationDir,
    ...(commandPath ? { commandPath } : {})
  };
}

function parseSkillMarkdown(text: string): { frontmatter: SkillFrontmatter; body: string } {
  const match = /^\uFEFF?---\r?\n([\s\S]*?)\r?\n---\r?\n?([\s\S]*)$/u.exec(text);
  if (!match) {
    throw new Error("SKILL.md must begin with YAML frontmatter");
  }

  const lines = match[1].split(/\r?\n/u);
  const parsed = new Map<string, string>();
  const metadata: Record<string, string> = {};
  let index = 0;
  while (index < lines.length) {
    const line = lines[index];
    if (!line.trim()) {
      index += 1;
      continue;
    }
    const separatorIndex = line.indexOf(":");
    if (separatorIndex < 0) {
      throw new Error(`invalid frontmatter line: ${line}`);
    }
    const key = line.slice(0, separatorIndex).trim();
    const value = line.slice(separatorIndex + 1).trim();
    if (key === "metadata") {
      index += 1;
      while (index < lines.length && lines[index].startsWith("  ")) {
        const metadataLine = lines[index].trim();
        const metadataSeparator = metadataLine.indexOf(":");
        if (metadataSeparator < 0) {
          throw new Error(`invalid metadata line: ${metadataLine}`);
        }
        const metadataKey = metadataLine.slice(0, metadataSeparator).trim();
        const metadataValue = metadataLine.slice(metadataSeparator + 1).trim();
        metadata[metadataKey] = parseFrontmatterScalar(metadataValue);
        index += 1;
      }
      continue;
    }
    parsed.set(key, parseFrontmatterScalar(value));
    index += 1;
  }

  const extras: Record<string, string> = {};
  for (const [key, value] of parsed.entries()) {
    if (!["name", "description", "compatibility", "license", "allowed-tools"].includes(key)) {
      extras[key] = value;
    }
  }

  return {
    frontmatter: {
      name: parsed.get("name") ?? "",
      description: parsed.get("description") ?? "",
      metadata,
      compatibility: parsed.get("compatibility"),
      license: parsed.get("license"),
      allowedTools: parsed.get("allowed-tools"),
      extras
    },
    body: match[2]
  };
}

function renderSkillMarkdown(frontmatter: SkillFrontmatter, body: string): string {
  const lines = ["---"];
  lines.push(`name: ${renderFrontmatterScalar(frontmatter.name)}`);
  lines.push(`description: ${renderFrontmatterScalar(frontmatter.description)}`);
  if (frontmatter.license !== undefined) {
    lines.push(`license: ${renderFrontmatterScalar(frontmatter.license)}`);
  }
  if (frontmatter.compatibility !== undefined) {
    lines.push(`compatibility: ${renderFrontmatterScalar(frontmatter.compatibility)}`);
  }
  if (frontmatter.allowedTools !== undefined) {
    lines.push(`allowed-tools: ${renderFrontmatterScalar(frontmatter.allowedTools)}`);
  }
  for (const key of Object.keys(frontmatter.extras ?? {}).sort()) {
    lines.push(`${key}: ${renderFrontmatterScalar(frontmatter.extras?.[key] ?? "")}`);
  }
  if (Object.keys(frontmatter.metadata).length) {
    lines.push("metadata:");
    for (const key of Object.keys(frontmatter.metadata).sort()) {
      lines.push(`  ${key}: ${renderFrontmatterScalar(frontmatter.metadata[key])}`);
    }
  }
  lines.push("---");
  lines.push("");
  lines.push(body.replace(/^\r?\n/u, ""));
  return `${lines.join("\n")}`;
}

function requireAppVersion(app: AclipApp, context: string): string {
  if (!app.version?.trim()) {
    throw new Error(`version is required when ${context}`);
  }
  return app.version;
}

function validateSkillFrontmatter(frontmatter: SkillFrontmatter): void {
  if (!frontmatter.name) {
    throw new Error("skill package frontmatter must define name");
  }
  if (!/^[a-z0-9]+(?:-[a-z0-9]+)*$/u.test(frontmatter.name)) {
    throw new Error("skill package name must use lowercase kebab-case");
  }
  if (!frontmatter.description) {
    throw new Error("skill package frontmatter must define description");
  }
}

function parseFrontmatterScalar(value: string): string {
  if (value.startsWith("\"") && value.endsWith("\"")) {
    return JSON.parse(value) as string;
  }
  if (value.startsWith("'") && value.endsWith("'")) {
    return value.slice(1, -1);
  }
  return value;
}

function renderFrontmatterScalar(value: string): string {
  if (!value) {
    return "\"\"";
  }
  if (/^[A-Za-z0-9._/@ -]+$/u.test(value) && !value.includes(":")) {
    return value;
  }
  return JSON.stringify(value);
}

function hasGroup(app: AclipApp, groupName: string): boolean {
  return app.commandGroups.some((commandGroup) => commandGroup.path.length === 1 && commandGroup.path[0] === groupName);
}

function findCommand(app: AclipApp, commandPath: string[]): CommandSpec {
  const command = app.commands.find(
    (candidate) =>
      candidate.path.length === commandPath.length &&
      candidate.path.every((segment, index) => segment === commandPath[index])
  );
  if (!command) {
    throw new Error(`unknown command path for skill export: ${commandPath.join(" ")}`);
  }
  return command;
}
