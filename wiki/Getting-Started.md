# Getting Started

## Install and launch

1. Open eDock.
2. Open Spotlight and search with `>Macro Studio`.
3. Install and enable the app if necessary.
4. Restart eDock when prompted.
5. Launch Macro Studio.

## Create a first macro

1. Keep the default `Main` macro or create a project title that describes the workflow.
2. Select the **Keyboard** category.
3. Add `keyboard.type_text` and enter a short test phrase.
4. Add `timing.wait` and give it a small delay.
5. Add `keyboard.key_press` with `enter` if the target application expects a submission.
6. Click **Run**.
7. Save the project from the header.

Start with harmless actions in a text editor. Once the sequence is reliable, replace the test actions with the real workflow.

## Before you automate a real task

- Confirm the target window is visible and focused.
- Check every command's values.
- Use a small loop count.
- Leave enough delay for applications to respond.
- Save a backup before adding file writes, system commands, or loops.
