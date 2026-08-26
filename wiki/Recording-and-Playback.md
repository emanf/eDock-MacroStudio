# Recording and Playback

## Record input

Click **Record**, perform the actions, then click **Stop Recording**. Macro Studio captures mouse moves, clicks, scrolls, key presses, and meaningful pauses.

Mouse movement is throttled during recording so the result remains editable. This means a recording is an approximation of the path, not a frame-by-frame capture.

## Refine the recording

After recording:

1. Remove accidental clicks and key presses.
2. Replace unnecessary mouse movement with a stable window or image-based command.
3. Adjust waits for the target application's response time.
4. Replace hard-coded text with variables when it will change.
5. Run one iteration before enabling loops or triggers.

## Run controls

- **Run** executes the `Main` macro.
- **Run Selected Macro** executes the active macro group.
- **Pause** temporarily suspends execution.
- Clicking the active run button again stops the current run.

The runtime also supports global hotkeys and timers through the corresponding commands. These can continue to trigger work while the editor is open, so unregister or remove them when they are no longer needed.
