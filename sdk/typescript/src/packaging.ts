import { chmodSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { resolve } from "node:path";
import { pathToFileURL } from "node:url";

import type { AclipApp } from "./app.js";

export interface CliArtifact {
  entryPath: string;
  manifestPath: string;
  manifest: Record<string, unknown>;
}

export interface BuildCliOptions {
  app: AclipApp;
  executableName: string;
  packageName: string;
  packageVersion: string;
  entryFile: string;
  projectRoot: string;
  outDir?: string;
}

/** @deprecated Use CliArtifact instead. */
export type NodeCliArtifact = CliArtifact;
/** @deprecated Use BuildCliOptions instead. */
export type PackageNodeCliOptions = BuildCliOptions;

export async function loadAppFactory(target: string): Promise<() => AclipApp> {
  const separator = target.lastIndexOf(":");
  if (separator <= 0) {
    throw new Error("app factory must use the form '<module-path>:<export-name>'");
  }

  const modulePath = target.slice(0, separator);
  const exportName = target.slice(separator + 1);
  const moduleUrl = pathToFileURL(resolve(modulePath)).href;
  const importedModule = (await import(moduleUrl)) as Record<string, unknown>;
  const factory = importedModule[exportName];

  if (typeof factory !== "function") {
    throw new Error("app factory target must resolve to a callable export");
  }

  return factory as () => AclipApp;
}

/**
 * @deprecated Use build_cli() instead.
 */
export async function packageNodeCli(options: PackageNodeCliOptions): Promise<CliArtifact> {
  return build_cli({
    app: options.app,
    executableName: options.executableName,
    packageName: options.packageName,
    packageVersion: options.packageVersion,
    entryFile: options.entryFile,
    projectRoot: options.projectRoot,
    outDir: options.outDir
  });
}

export async function build_cli(
  options: {
    app: AclipApp;
    entryFile: string;
    projectRoot: string;
    outDir?: string;
    executableName?: string;
    packageName?: string;
    packageVersion?: string;
  }
): Promise<CliArtifact> {
  const { build } = await import("tsup");
  const outDir = options.outDir ?? resolve(options.projectRoot, "dist");
  mkdirSync(outDir, { recursive: true });
  const packageMetadata = readPackageMetadata(options.projectRoot);
  const executableName = options.executableName ?? options.app.name;
  const packageName = options.packageName ?? packageMetadata.name;
  const packageVersion = options.packageVersion ?? packageMetadata.version;

  await build({
    entry: {
      [executableName]: options.entryFile
    },
    outDir,
    format: ["cjs"],
    platform: "node",
    target: "node22",
    clean: true,
    dts: false,
    sourcemap: false,
    silent: true,
    splitting: false,
    noExternal: ["commander"],
    banner: {
      js: "#!/usr/bin/env node"
    }
  });

  const entryPath = resolve(outDir, `${executableName}.cjs`);
  try {
    chmodSync(entryPath, 0o755);
  } catch {
    // chmod is best-effort on Windows
  }

  const manifest = options.app.buildIndexManifest({
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
