import type { AclipApp } from "./app.js";

export type CliAppTarget =
  | AclipApp
  | (() => AclipApp)
  | (() => Promise<AclipApp>)
  | string;

export async function resolveApp(target: CliAppTarget): Promise<AclipApp> {
  if (typeof target === "string") {
    const { loadAppTarget } = await import("./packaging.js");
    return loadAppTarget(target);
  }
  if (typeof target === "function") {
    return await target();
  }
  return target;
}

export async function cliMain(
  target: CliAppTarget,
  argv: string[] = process.argv.slice(2)
): Promise<number> {
  const exitCode = await (await resolveApp(target)).run(argv);
  process.exitCode = exitCode;
  return exitCode;
}

export const runCli = cliMain;
