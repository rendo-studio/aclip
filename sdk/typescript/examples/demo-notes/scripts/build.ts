import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

import { build_cli } from "../../../src/index.js";

const currentDir = fileURLToPath(new URL(".", import.meta.url));
const exampleRoot = resolve(currentDir, "..");

await build_cli({
  appFactory: "./src/app.ts:createApp",
  projectRoot: exampleRoot,
  outDir: resolve(exampleRoot, "dist")
});
