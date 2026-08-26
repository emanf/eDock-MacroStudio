import re

from ...core.model.macro_command import MacroCommand, ResultPolicy
from ...core.model.macro_category import MacroCommandCategory


FilesCategory = MacroCommandCategory("files", "Files", "mc:e2c7")


class SearchRegexInFileCommand(MacroCommand):
    id = "files.search_regex_in_file"
    title = "Search Regex In File"
    category = FilesCategory
    icon = "mc:e8b6"
    description = "Search by regex in a file and save matched lines and indexes into a variable."
    result_policy = ResultPolicy.DATA
    fields = [
        {
            "name": "path",
            "title": "File",
            "place_holder": "File path",
            "value_type": "file",
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
            "name": "encoding",
            "title": "Encoding",
            "place_holder": "utf-8",
            "value_type": "string",
            "default_value": "utf-8",
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
            "place_holder": "search_result",
            "value_type": "variable",
            "default_value": "",
        },
    ]

    def display_text(self, values=None):
        values = self.normalize_values(values)
        return f"search regex {values.get('pattern')} in {values.get('path')} to {values.get('variable_name')}"

    def execute(self, values=None, runtime=None):
        values = self.normalize_values(values)
        path = str(values.get("path", "") or "")
        pattern = str(values.get("pattern", ".*") or ".*")
        encoding = str(values.get("encoding", "utf-8") or "utf-8")
        ignore_case = bool(values.get("ignore_case", False))
        variable_name = values.get("variable_name")
        flags = re.IGNORECASE if ignore_case else 0

        try:
            regex = re.compile(pattern, flags)
        except re.error as e:
            raise ValueError(f"Invalid regex pattern: {pattern}\n{e}")

        matches = []

        with open(path, "r", encoding=encoding) as file:
            for line_index, line in enumerate(file.readlines()):
                clean_line = line.rstrip("\n")
                for match in regex.finditer(clean_line):
                    matches.append({
                        "line": clean_line,
                        "line_index": line_index,
                        "line_number": line_index + 1,
                        "start": match.start(),
                        "end": match.end(),
                        "text": match.group(0),
                        "groups": list(match.groups()),
                        "groupdict": match.groupdict(),
                    })

        result = {
            "path": path,
            "pattern": pattern,
            "count": len(matches),
            "matches": matches,
        }

        if variable_name:
            runtime.vars.set(variable_name, result)

        return result


def register_macro(registry):
    registry.register(SearchRegexInFileCommand)
