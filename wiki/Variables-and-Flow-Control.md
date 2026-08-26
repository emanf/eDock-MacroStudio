# Variables and Flow Control

## Variables

Open **Variables** to define project-level values. Variables are useful for paths, names, counters, URLs, and other values shared by several commands.

The command library includes variable creation and checking, random values, numeric calculations, and text operations. Prefer variables over duplicating the same literal value throughout a project.

## Flow control

The flow-control family includes commands for:

- Starting and stopping loops
- Ending a loop
- Conditional jumps
- Running another macro group
- Jumping to a comment or marker
- Stopping the current run or the entire run

Keep nested calls shallow and use **Max Depth** as a guard against accidental recursion. Give groups and comments descriptive names so the execution path is understandable when you revisit the project.
