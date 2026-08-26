# Troubleshooting

## Recording fails

Install the app requirements with `pip install -r requirements.txt`, then verify that `pynput` can access keyboard and mouse events. Some operating systems require explicit input-monitoring permission.

## A command is not listed

Check the category first. If it is still missing, the command module may have failed to import or may be unavailable on the current operating system. Review the eDock console output for the traceback.

## Playback is too fast or unreliable

Increase **Delay ms**, lower **Speed**, and add explicit `timing.wait` commands after actions that open windows, load files, or trigger network work.

## Coordinates no longer match

Recorded coordinates depend on display resolution, scaling, window position, and application state. Prefer window discovery or screen-recognition commands when a workflow must survive layout changes.

## A project is missing

Look in the Macro Studio app-data `projects/` directory. Standalone macro groups are in `macros/`. If you moved the eDock installation, make sure you are checking the app-data directory used by the active eDock instance.

## Global triggers keep firing

Stop the current run and remove or disable the `register_hotkey` or `register_timer` item. Restarting eDock is also a safe way to clear a stale runtime.
