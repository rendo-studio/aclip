import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

import { export_skills } from "../../../src/index.js";
import { createApp } from "../src/app.js";

const currentDir = fileURLToPath(new URL(".", import.meta.url));
const exampleRoot = resolve(currentDir, "..");
const skillsRoot = resolve(exampleRoot, "skills");

const app = createApp();
app.addCliSkill(resolve(skillsRoot, "notes-overview"));
app.addCommandSkill(["note", "create"], resolve(skillsRoot, "note-create-best-practice"));

const artifact = await export_skills(app, {
  outDir: resolve(exampleRoot, "dist", "skills")
});

console.log(artifact.indexPath);
