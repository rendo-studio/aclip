import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

import { packageNodeCli } from "../../../src/index.js";
import { createApp } from "../src/app.js";

const currentDir = fileURLToPath(new URL(".", import.meta.url));
const exampleRoot = resolve(currentDir, "..");
const sdkRoot = resolve(exampleRoot, "..", "..");

await packageNodeCli({
  app: createApp(),
  executableName: "aclip-demo-notes",
  packageName: "@aclip/demo-notes",
  packageVersion: "0.1.0",
  entryFile: resolve(exampleRoot, "src", "cli.ts"),
  projectRoot: sdkRoot,
  outDir: resolve(exampleRoot, "dist")
});
