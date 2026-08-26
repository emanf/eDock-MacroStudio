# Macro Studio Wiki

Welcome to the Macro Studio documentation. Macro Studio is an eDock app for building, recording, organizing, and running desktop automation macros.

## Start here

- [Getting Started](Getting-Started.md) — install the app and build your first working macro.
- [Building Macros](Building-Macros.md) — understand commands, items, macro groups, and editing.
- [Recording and Playback](Recording-and-Playback.md) — record input and tune execution safely.
- [Variables and Flow Control](Variables-and-Flow-Control.md) — create reusable, conditional workflows.
- [Command Reference](Command-Reference.md) — browse the built-in command families.
- [Projects and Storage](Projects-and-Storage.md) — understand project files, standalone macros, and app data.
- [Custom Commands](Custom-Commands.md) — extend Macro Studio with Python modules.
- [Troubleshooting](Troubleshooting.md) — diagnose dependency, permissions, and playback issues.

## A useful mental model

```text
Project
└── Macro groups
    └── Macro items
        └── Command + values + enabled state
```

The `Main` macro is the project's entry point. Additional macro groups can be called from other groups, which keeps larger automations readable and reusable.
