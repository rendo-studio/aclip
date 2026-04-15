import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

import * as aclip from "../../../src/index.js";

const currentDir = fileURLToPath(new URL(".", import.meta.url));
const exampleRoot = resolve(currentDir, "..");

await aclip.build("./src/app.ts:app", {
  projectRoot: exampleRoot,
  outDir: resolve(exampleRoot, "dist")
});
