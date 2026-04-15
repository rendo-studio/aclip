import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

import { createApp } from "../src/app.js";

const currentDir = fileURLToPath(new URL(".", import.meta.url));
const exampleRoot = resolve(currentDir, "..");

await createApp().build_cli({
  entryFile: resolve(exampleRoot, "src", "cli.ts"),
  projectRoot: exampleRoot,
  outDir: resolve(exampleRoot, "dist")
});
