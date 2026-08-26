import os
import re

from ...core.model.macro_command import MacroCommand, ResultPolicy
from ...core.model.macro_category import MacroCommandCategory


FilesCategory = MacroCommandCategory("files", "Files", "mc:e2c7")


class FindPathsByRegexCommand(MacroCommand):
    id = "files.find_paths_by_regex"
    title = "Find Files/Folders By Regex"
    category = FilesCategory
    icon = "mc:e8b6"
    description = "Find files or folders by regex and save paths into a variable."
    result_policy = ResultPolicy.DATA
    fields = [
        {
            "name": "root",
            "title": "Root Folder",
            "place_holder": "Root folder",
            "value_type": "folder",
            "default_value": "",
        },
        {
            "name": "pattern",
            "title": "Regex",
            "place_holder": "Pattern",
            "value_type": "string",
            "default_value": ".*",
        },
        {
            "name": "target",
            "title": "Target",
            "value_type": "choice",
            "options": ["files", "folders", "both"],
            "default_value": "files",
        },
        {
            "name": "recursive",
            "title": "Recursive",
            "value_type": "bool",
            "default_value": True,
        },
        {
            "name": "ignore_case",
            "title": "Ignore Case",
            "value_type": "bool",
            "default_value": False,
        },
        {
            "name": "variable_name",
            "title": "Save To Variable",
            "place_holder": "found_paths",
            "value_type": "variable",
            "default_value": "",
        },
    ]

    def display_text(self, values=None):
        values = self.normalize_values(values)
        return f"find {values.get('target')} by {values.get('pattern')} in {values.get('root')} to {values.get('variable_name')}"

    def execute(self, values=None, runtime=None):
        values = self.normalize_values(values)
        root = str(values.get("root", "") or "")
        pattern = str(values.get("pattern", ".*") or ".*")
        target = str(values.get("target", "files") or "files")
        recursive = bool(values.get("recursive", True))
        ignore_case = bool(values.get("ignore_case", False))
        variable_name = values.get("variable_name")
        flags = re.IGNORECASE if ignore_case else 0

        try:
            regex = re.compile(pattern, flags)
        except re.error as e:
            raise ValueError(f"Invalid regex pattern: {pattern}\n{e}")

        paths = []

        if recursive:
            for current_root, folders, files in os.walk(root):
                if target in ["folders", "both"]:
                    for folder_name in folders:
                        if regex.search(folder_name):
                            paths.append(os.path.join(current_root, folder_name))

                if target in ["files", "both"]:
                    for file_name in files:
                        if regex.search(file_name):
                            paths.append(os.path.join(current_root, file_name))
        else:
            for item_name in os.listdir(root):
                item_path = os.path.join(root, item_name)

                if os.path.isfile(item_path) and target in ["files", "both"] and regex.search(item_name):
                    paths.append(item_path)

                if os.path.isdir(item_path) and target in ["folders", "both"] and regex.search(item_name):
                    paths.append(item_path)

        result = {
            "root": root,
            "pattern": pattern,
            "target": target,
            "recursive": recursive,
            "count": len(paths),
            "paths": paths,
        }

        if variable_name:
            runtime.vars.set(variable_name, result)

        return result


def register_macro(registry):
    registry.register(FindPathsByRegexCommand)
