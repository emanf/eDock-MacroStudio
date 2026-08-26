# Building Macros

## Add commands

Choose a category, then add a command from the **Commands** panel. Commands can be dragged into the macro list. Each added item stores the command id, its values, and whether it is enabled.

## Edit and organize

The macro list supports:

- Editing command values
- Reordering items
- Copy, cut, and paste
- Delete
- Enable or disable an item without removing it
- Undo and redo

Use comments and separate macro groups to make long workflows easier to maintain.

## Macro groups

Every project has a `Main` group. Add more groups for reusable units such as `Login`, `Prepare Files`, or `Clean Up`. A flow-control command can run another macro group, including nested groups.

Macro titles are for people; safe names are used internally when projects are saved. Renaming a group updates references maintained by Macro Studio.

## Execution settings

The control bar provides:

- **Loop** — number of times to run the selected sequence.
- **Speed** — playback multiplier; values below `1` slow a macro down and values above `1` speed it up.
- **Delay ms** — extra delay applied between execution steps.
- **Max Depth** — safety limit for nested macro calls.

Use conservative values while testing. A faster macro is not always a more reliable macro.
