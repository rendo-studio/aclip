import type { AclipApp } from "./app.js";

export type CliAppTarget =
  | AclipApp
  | (() => AclipApp)
  | (() => Promise<AclipApp>);

export async function resolveApp(target: CliAppTarget): Promise<AclipApp> {
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
