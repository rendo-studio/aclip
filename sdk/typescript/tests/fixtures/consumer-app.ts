import { AclipApp, stringArgument } from "@rendo-studio/aclip";

export function createApp() {
  const app = new AclipApp({
    name: "consumer-fixture",
    version: "0.1.0",
    summary: "Consumer packaging fixture.",
    description: "Validates ACLIP packaging from a consumer-style root import."
  });

  app.command("status", {
    summary: "Report status",
    description: "Return a small status payload.",
    arguments: [
      stringArgument("store", {
        description: "Unused optional store path.",
        defaultValue: ".consumer-fixture.json"
      })
    ],
    examples: ["consumer-fixture status"],
    handler: ({ store }) => ({
      status: "ok",
      store: String(store ?? ".consumer-fixture.json")
    })
  });

  return app;
}

export const app = createApp();
