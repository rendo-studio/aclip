import { Command } from "commander";
import { basename, resolve } from "node:path";

import { build_cli, loadAppFactory } from "./packaging.js";

export async function main(argv = process.argv): Promise<void> {
  const program = new Command()
    .name("aclip-build-cli")
    .requiredOption("--app-factory <target>", "App factory in the form './src/app.ts:createApp'.")
    .requiredOption("--entry-file <path>", "CLI entry file to bundle.")
    .option("--name <name>", "Executable name. Defaults to the ACLIP app name.")
    .option("--project-root <path>", "Project root used to resolve relative inputs.", ".")
    .option("--out-dir <path>", "Output directory for the bundled artifact and sidecar manifest.")
    .option("--package-name <name>", "npm package name to write into distribution metadata.")
    .option("--package-version <version>", "Package version to write into distribution metadata.");

  program.parse(argv);
  const options = program.opts<{
    appFactory: string;
    entryFile: string;
    name?: string;
    projectRoot: string;
    outDir?: string;
    packageName?: string;
    packageVersion?: string;
  }>();

  const projectRoot = resolve(options.projectRoot);
  const entryFile = resolve(projectRoot, options.entryFile);
  const factory = await loadAppFactory(resolveAppFactoryTarget(projectRoot, options.appFactory));
  const artifact = await build_cli({
    app: factory(),
    entryFile,
    projectRoot,
    outDir: options.outDir ? resolve(projectRoot, options.outDir) : undefined,
    executableName: options.name,
    packageName: options.packageName,
    packageVersion: options.packageVersion
  });

  process.stdout.write(`${artifact.entryPath}\n${artifact.manifestPath}\n`);
}

function resolveAppFactoryTarget(projectRoot: string, target: string): string {
  const separator = target.lastIndexOf(":");
  if (separator <= 0) {
    return target;
  }

  const modulePath = target.slice(0, separator);
  const exportName = target.slice(separator + 1);
  return `${resolve(projectRoot, modulePath)}:${exportName}`;
}

const invokedPath = process.argv[1];
if (invokedPath && /^buildCliCli\.(ts|js|cjs)$/.test(basename(invokedPath))) {
  void main().catch((error: unknown) => {
    const message = error instanceof Error ? error.message : String(error);
    process.stderr.write(`${message}\n`);
    process.exitCode = 1;
  });
}
