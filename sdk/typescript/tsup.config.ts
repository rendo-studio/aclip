import { defineConfig } from "tsup";

export default defineConfig([
  {
    entry: ["src/index.ts"],
    format: ["esm"],
    dts: true,
    sourcemap: true,
    clean: true,
    target: "node22"
  },
  {
    entry: ["src/buildCliCli.ts"],
    format: ["cjs"],
    dts: false,
    sourcemap: true,
    clean: false,
    target: "node22",
    outExtension: () => ({
      js: ".cjs"
    }),
    banner: {
      js: "#!/usr/bin/env node"
    }
  }
]);
