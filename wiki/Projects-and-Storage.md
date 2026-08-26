# Projects and Storage

## Project files

Macro Studio saves projects as readable JSON with:

- Project title and safe name
- Project-level variables
- Execution settings
- Active macro
- All macro groups and their items

The file format identifies itself as `macro_studio_project` and currently uses version `1`.

## Standalone macro groups

Macro tabs can save an individual macro group. This is useful for building a reusable routine or sharing a small automation without the rest of a project.

## App-data layout

Macro Studio creates these directories below its eDock app-data directory:

```text
<eDock app data>/emanf.macro-studio/
├── projects/   # complete project JSON files
├── macros/     # standalone macro-group JSON files
└── commands/   # user-provided Python command modules
```

Back up these directories before changing machines or making large edits.
