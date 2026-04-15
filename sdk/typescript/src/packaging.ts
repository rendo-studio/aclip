import { spawnSync } from "node:child_process";
import { randomUUID } from "node:crypto";
import { chmodSync, mkdirSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { createRequire } from "node:module";
import { basename, dirname, extname, relative, resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

import type { AclipApp } from "./app.js";

export interface CliArtifact {
  entryPath: string;
  manifestPath: string;
  manifest: Record<string, unknown>;
}

export interface BuildCliOptions {
  factory?: string;
  appFactory?: string;
  projectRoot?: string;
  outDir?: string;
  executableName?: string;
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
  const launcherFile = writeLauncherFile(tempDir, factoryInfo, defaultSdkImportSpecifier());
  const launcherEntry = relativeImportPath(projectRoot, launcherFile);
  const packageMetadata = readPackageMetadata(projectRoot);
  const executableName = normalizedOptions.executableName ?? app.name;
  const packageName = normalizedOptions.packageName ?? packageMetadata.name;
  const packageVersion = normalizedOptions.packageVersion ?? packageMetadata.version;
  const tsupConfigFile = writeTsupConfigFile(tempDir, {
    executableName,
    launcherEntry,
    outDir,
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

  const entryPath = resolve(outDir, `${executableName}.cjs`);
  try {
    chmodSync(entryPath, 0o755);
  } catch {
    // chmod is best-effort on Windows
  }

  const manifest = app.buildIndexManifest({
    binaryName: executableName,
    distribution: [
      {
        kind: "npm_package",
        package: packageName,
        version: packageVersion,
        executable: executableName
      }
    ]
  });
  const manifestPath = resolve(outDir, `${executableName}.aclip.json`);
  writeFileSync(manifestPath, JSON.stringify(manifest, null, 2), "utf8");

  return {
    entryPath,
    manifestPath,
    manifest
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

function readPackageMetadata(projectRoot: string): { name: string; version: string } {
  const packageJsonPath = resolve(projectRoot, "package.json");
  const packageJson = JSON.parse(readFileSync(packageJsonPath, "utf8")) as {
    name?: string;
    version?: string;
  };
  if (!packageJson.name || !packageJson.version) {
    throw new Error("package.json must define name and version for build_cli defaults");
  }
  return {
    name: packageJson.name,
    version: packageJson.version
  };
}

function defaultSdkImportSpecifier(): string {
  const currentFile = fileURLToPath(import.meta.url);
  const indexFile = currentFile.endsWith(".ts") ? "index.ts" : "index.js";
  return resolve(dirname(currentFile), indexFile);
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
    executableName: string;
    launcherEntry: string;
    outDir: string;
  },
): string {
  const configPath = resolve(tempDir, "tsup.build.config.ts");
  writeFileSync(
    configPath,
    [
      'import { defineConfig } from "tsup";',
      "",
      "export default defineConfig({",
      `  entry: { ${JSON.stringify(options.executableName)}: ${JSON.stringify(options.launcherEntry)} },`,
      `  outDir: ${JSON.stringify(options.outDir)},`,
      '  format: ["cjs"],',
      '  platform: "node",',
      '  target: "node22",',
      "  clean: true,",
      "  dts: false,",
      "  sourcemap: false,",
      "  silent: true,",
      "  splitting: false,",
      '  noExternal: ["commander"],',
      '  banner: { js: "#!/usr/bin/env node" },',
      "});",
      "",
    ].join("\n"),
    "utf8",
  );
  return configPath;
}

export const build = build_cli;
