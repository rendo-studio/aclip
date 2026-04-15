import { existsSync, readFileSync, writeFileSync } from "node:fs";

import { AclipApp } from "../../../src/app.js";
import { stringArgument } from "../../../src/contracts.js";

interface NoteRecord {
  title: string;
  body: string;
}

function loadNotes(store: string): NoteRecord[] {
  if (!existsSync(store)) {
    return [];
  }
  return JSON.parse(readFileSync(store, "utf8")) as NoteRecord[];
}

function saveNotes(store: string, notes: NoteRecord[]): void {
  writeFileSync(store, JSON.stringify(notes, null, 2), "utf8");
}

export function createApp(): AclipApp {
  const app = new AclipApp({
    name: "aclip-demo-notes",
    version: "0.1.0",
    summary: "Example notes CLI built with the aclip SDK",
    description: "Stores notes in a local JSON file and exposes agent-first command disclosure."
  });

  const note = app.group("note", {
    summary: "Manage notes",
    description: "Create and list notes in the local JSON store."
  });

  note.command("create", {
    summary: "Create a note",
    description: "Create a note in a local JSON store.",
    arguments: [
      stringArgument("title", { required: true, description: "Title for the note." }),
      stringArgument("body", { required: true, description: "Body text for the note." }),
      stringArgument("store", {
        description: "Path to the local note store.",
        defaultValue: ".aclip-demo-notes.json"
      })
    ],
    examples: ["aclip-demo-notes note create --title hello --body world"],
    handler: (payload) => {
      const title = String(payload.title);
      const body = String(payload.body);
      const store = String(payload.store ?? ".aclip-demo-notes.json");
      const notes = loadNotes(store);
      const noteRecord = { title, body };
      notes.push(noteRecord);
      saveNotes(store, notes);
      return {
        note: noteRecord,
        store
      };
    }
  });

  note.command("list", {
    summary: "List notes",
    description: "List notes from the local JSON store.",
    arguments: [
      stringArgument("store", {
        description: "Path to the local note store.",
        defaultValue: ".aclip-demo-notes.json"
      })
    ],
    examples: ["aclip-demo-notes note list"],
    handler: (payload) => {
      const store = String(payload.store ?? ".aclip-demo-notes.json");
      return {
        notes: loadNotes(store),
        store
      };
    }
  });

  return app;
}
