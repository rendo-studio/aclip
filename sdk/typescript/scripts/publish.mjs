import { spawnSync } from "node:child_process";
import { mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { fileURLToPath } from "node:url";

const packageRoot = fileURLToPath(new URL("..", import.meta.url));
const npmCommand = "npm";

function run(command, args, extra = {}) {
  const result = spawnSync(command, args, {
    cwd: packageRoot,
    stdio: "inherit",
    shell: process.platform === "win32",
    ...extra
  });
  if (result.error) {
    console.error(result.error.message);
    process.exit(1);
  }
  if (result.status !== 0) {
    process.exit(result.status ?? 1);
  }
}

function check() {
  run(npmCommand, ["test"]);
  run(npmCommand, ["run", "check"]);
  run(npmCommand, ["run", "build"]);
  run(npmCommand, ["publish", "--dry-run", "--access", "public"]);
}

function publish() {
  const token = process.env.NPM_TOKEN;
  if (!token) {
    console.error("NPM_TOKEN is required.");
    process.exit(1);
  }

  check();

  const tempDir = mkdtempSync(join(tmpdir(), "aclip-npm-"));
  const userConfigPath = join(tempDir, ".npmrc");
  writeFileSync(
    userConfigPath,
    "registry=https://registry.npmjs.org/\n//registry.npmjs.org/:_authToken=${NODE_AUTH_TOKEN}\n",
    "utf8"
  );

  try {
    run(npmCommand, ["publish", "--access", "public", "--userconfig", userConfigPath], {
      env: {
        ...process.env,
        NODE_AUTH_TOKEN: token
      }
    });
  } finally {
    rmSync(tempDir, { recursive: true, force: true });
  }
}

const command = process.argv[2];

if (command === "check") {
  check();
} else if (command === "publish") {
  publish();
} else {
  console.error("Usage: node ./scripts/publish.mjs <check|publish>");
  process.exit(1);
}
