<p align="center"><img src="ss_macro_studio.png?v=2" width="600" alt="Macro Studio"></p>

# Macro Studio

Macro Studio is a visual automation workspace for [eDock](https://github.com/emanf/eDock). It gives you a practical way to turn repetitive desktop work into reusable macros: build a sequence of commands, record real mouse and keyboard activity, add variables and flow control, then run the result with precise execution settings.

It is designed for people who want more control than a one-off script, without having to hand-write every automation step.

## What you can build

- Repetitive desktop workflows
- Keyboard and mouse sequences
- File and text-processing helpers
- Window-management routines
- Dialog-driven utilities
- Timed or looped tasks
- Reusable macro groups called from other macros
- Small Python-powered extensions for commands that are specific to your workflow

## Highlights

- **Visual macro editor** — browse commands by category and add them to the active macro.
- **Recording** — capture mouse movement, clicks, scrolling, key presses, and the pauses between actions.
- **Multiple macro groups** — keep a project organized with a `Main` macro and additional reusable groups.
- **Variables** — define project values and use them across commands.
- **Flow control** — loops, conditions, jumps, nested macro calls, and explicit stop commands.
- **Execution controls** — configure loop count, playback speed, delay between actions, and maximum nesting depth.
- **Pause and stop** — pause a running macro or stop the current run from the control bar.
- **Undo and redo** — safely experiment while editing a macro.
- **Enable/disable items** — temporarily skip a command without deleting it.
- **Projects and standalone macros** — save a complete project or save an individual macro group for reuse.
- **Extensible command registry** — built-in commands are loaded automatically, and user command modules can be added from app data.

## Install

Macro Studio runs inside eDock.

1. Open [eDock](https://github.com/emanf/eDock).
2. Open Spotlight and type `>Macro Studio`.
3. Install and enable Macro Studio if it is not already installed.
4. Restart eDock when requested.
5. Launch Macro Studio from your enabled apps.

If you are developing eDock locally, place this app under the repository's `apps/` directory and make sure the app is enabled in the eDock user configuration.

## Quick start

1. Open Macro Studio and give the project a useful title.
2. Choose a category in the left panel.
3. Add commands from the **Commands** panel to the active macro. You can drag commands into the macro list or use the command action.
4. Select a command in the macro list to edit its values.
5. Use **Variables** when a value should be reused or changed without editing every command.
6. Click **Run** to execute the `Main` macro, or **Run Selected Macro** to execute the current macro group.
7. Use **Pause** or the run button again to stop an execution.
8. Save the project when the workflow is ready to keep.

For a first experiment, combine `mouse.click`, `keyboard.type_text`, and `timing.wait`. Start with a short workflow and verify each step before adding loops or global triggers.

## The editor at a glance

| Area | Purpose |
| --- | --- |
| Title bar | Create a new project, open a saved project, save the current project, and edit its title |
| Control bar | Run, run the selected macro, pause/stop, record, and configure execution |
| Categories | Filter the command library |
| Commands | Browse available commands and add them to the active macro |
| Macro tabs | Switch between the project's macro groups |
| Macro list | Edit, reorder, copy, cut, paste, delete, enable, or disable individual items |
| Variables | Define project-level values used by commands |

## Command library

The built-in library is organized into these categories:

`audio` · `clipboard` · `dialogs` · `files` · `flow_control` · `keyboard` · `mouse` · `network` · `numbers` · `screen_recognition` · `system` · `text` · `timing` · `variables` · `windows`

Examples include:

- Clipboard read/write and paste operations
- File copying, reading, writing, and regular-expression searches
- Text formatting, replacement, extraction, splitting, and joining
- Mouse movement, clicking, and scrolling
- Keyboard key presses, hotkeys, and text entry
- Window discovery, positioning, resizing, opacity, and state changes
- File/folder pickers and confirmation or input dialogs
- Image and pixel-based screen recognition
- Python, shell/command, and URL launching
- Random values, calculations, timers, and waits

The exact fields shown for a command depend on that command. Some commands are operating-system-specific or require an optional dependency.

## Recording

Click **Record**, perform the actions you want to capture, then click **Stop Recording**. Macro Studio records:

- Mouse movement (throttled to keep recordings usable)
- Mouse clicks and scrolls
- Keyboard presses
- Wait commands for meaningful pauses between actions

Recording is a starting point, not a finished macro. Review coordinates, waits, text, and window assumptions before relying on the result. For a more robust workflow, replace fragile recorded coordinates with window, image, or variable-based logic where appropriate.

## Projects, macro groups, and storage

A project contains:

- A project title and safe file name
- One or more macro groups
- Project-level variables
- Execution settings
- The active macro selection

Projects are stored as readable JSON. Macro Studio stores project files and standalone macro groups below its eDock app-data directory:

```text
<eDock app data>/emanf.macro-studio/
├── projects/
├── macros/
└── commands/
```

The `commands/` directory is also the extension point for user-defined command modules. Keep backups of important project files before making large changes.

## Custom commands

Macro Studio loads Python modules placed in the app-data `commands/` directory. A module must expose a callable named `register_macro(registry)` and register one or more command classes with the provided registry.

This makes it possible to keep application-specific automation separate from the built-in command library. Custom commands execute with the same permissions as eDock, so only load code you trust.

## Safety and reliability

Macros can click, type, move windows, write files, launch programs, and execute Python or system commands. Before running an unfamiliar macro:

- Read the command list from top to bottom.
- Test with a low loop count and no extra delay reduction.
- Keep destructive file operations pointed at a safe test directory.
- Avoid leaving global hotkeys or timers registered in a project you are not actively using.
- Save a copy of the project before major edits.

Screen coordinates and image recognition can be affected by display scaling, window placement, theme changes, and resolution changes.

## Troubleshooting

**Recording does not start**  
Make sure the Python environment has `pynput` installed and that the operating system allows input monitoring.

**A command is missing**  
Check its category, confirm the command module loaded without an import error, and verify any optional dependency required by that command.

**A macro behaves differently on another machine**  
Review coordinates, display scaling, file paths, window titles, permissions, and OS-specific commands.

**A project does not appear where expected**  
Use Macro Studio's app-data directory for the active eDock installation. Project files are under `projects/`; standalone macro groups are under `macros/`.

## Development

The app is a Python eDock app. Its UI is built with PySide6; input recording uses `pynput`, and additional capabilities use packages listed in `requirements.txt`.

Install the app dependencies in the environment used by eDock:

```bash
pip install -r requirements.txt
```

Keep changes inside the app directory when possible, follow the existing command model, and test both editing and execution paths.

## License

No license.

## Wiki

The repository wiki content is maintained in [Wiki](https://github.com/emanf/eDock-MacroStudio/wiki). Start with [Getting Started](https://github.com/emanf/eDock-MacroStudio/wiki/Getting-Started.md), then continue to [Building Macros](https://github.com/emanf/eDock-MacroStudio/wiki/Building-Macros.md).
