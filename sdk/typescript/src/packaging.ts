import { chmodSync, mkdirSync, writeFileSync } from "node:fs";
import { resolve } from "node:path";
import { pathToFileURL } from "node:url";

import type { AclipApp } from "./app.js";

export interface NodeCliArtifact {
  entryPath: string;
  manifestPath: string;
  manifest: Record<string, unknown>;
}

export interface PackageNodeCliOptions {
  app: AclipApp;
  executableName: string;
  packageName: string;
  packageVersion: string;
  entryFile: string;
  projectRoot: string;
  outDir?: string;
}

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

export async function packageNodeCli(options: PackageNodeCliOptions): Promise<NodeCliArtifact> {
  const { build } = await import("tsup");
  const outDir = options.outDir ?? resolve(options.projectRoot, "dist");
  mkdirSync(outDir, { recursive: true });

  await build({
    entry: {
      [options.executableName]: options.entryFile
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

  const entryPath = resolve(outDir, `${options.executableName}.cjs`);
  try {
    chmodSync(entryPath, 0o755);
  } catch {
    // chmod is best-effort on Windows
  }

  const manifest = options.app.buildIndexManifest({
    binaryName: options.executableName,
    distribution: [
      {
        kind: "npm_package",
        package: options.packageName,
        version: options.packageVersion,
        executable: options.executableName
      }
    ]
  });
  const manifestPath = resolve(outDir, `${options.executableName}.aclip.json`);
  writeFileSync(manifestPath, JSON.stringify(manifest, null, 2), "utf8");

  return {
    entryPath,
    manifestPath,
    manifest
  };
}
