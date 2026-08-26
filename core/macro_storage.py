import json
import re
from pathlib import Path

from .model.macro_group import MacroGroup
from .model.macro_project import MacroProject


class MacroStorage:
    def __init__(self, app_ref):
        self.app_ref = app_ref

    def data_dir(self):
        path = self.app_ref.get_app_data_dir()
        path.mkdir(parents=True, exist_ok=True)
        return path

    def macros_dir(self):
        path = self.data_dir() / "macros"
        path.mkdir(parents=True, exist_ok=True)
        return path

    def projects_dir(self):
        path = self.data_dir() / "projects"
        path.mkdir(parents=True, exist_ok=True)
        return path

    def safe_name(self, value):
        value = str(value or "").strip().lower()
        value = re.sub(r"[^a-z0-9_\-]+", "_", value)
        value = re.sub(r"_+", "_", value).strip("_")
        return value or "untitled_macro"

    def macro_path(self, name):
        safe = self.safe_name(name)
        return self.macros_dir() / f"{safe}.json"

    def project_path(self, name):
        safe = self.safe_name(name)
        return self.projects_dir() / f"{safe}.json"

    def save_group(self, group):
        if not isinstance(group, MacroGroup):
            group = MacroGroup.from_json(group)

        if not group.name:
            group.name = self.safe_name(group.title)

        path = self.macro_path(group.name)
        path.write_text(
            json.dumps(group.to_json(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        return path

    def load_group(self, path):
        path = Path(path)
        if not path.exists():
            return MacroGroup()

        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return MacroGroup.from_json(data)
        except Exception:
            return MacroGroup()

    def save_project(
        self,
        path,
        title,
        name,
        macros,
        active_macro,
        variables,
        execution,
    ):
        project_macros = []

        for macro in macros or []:
            if not isinstance(macro, MacroGroup):
                macro = MacroGroup.from_json(macro)

            if not macro.name:
                macro.name = self.safe_name(macro.title)

            data = macro.to_json()
            data.pop("variables", None)
            project_macros.append(data)

        project_data = {
            "type": "macro_studio_project",
            "version": 1,
            "name": self.safe_name(name or title or "untitled_project"),
            "title": str(title or "Untitled Project").strip()
            or "Untitled Project",
            "active_macro": str(active_macro or "").strip(),
            "variables": self.normalize_variables(variables),
            "execution": MacroProject.normalize_execution(execution),
            "macros": project_macros,
        }

        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(project_data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        return path

    def load_project(self, path):
        path = Path(path)
        if not path.exists():
            return self.empty_project()

        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return self.empty_project()

        if not isinstance(data, dict):
            return self.empty_project()

        if "macros" not in data:
            group = MacroGroup.from_json(data)
            if not group.title:
                group.title = "Main"
            if not group.name:
                group.name = self.safe_name(group.title)

            return {
                "name": self.safe_name(
                    group.name or "untitled_project"
                ),
                "title": group.title or "Untitled Project",
                "variables": self.normalize_variables(group.variables),
                "execution": MacroProject.default_execution(),
                "macros": [
                    MacroGroup(
                        name=group.name,
                        title=group.title,
                        items=group.items,
                        variables=[],
                    )
                ],
                "active_macro": group.name,
            }

        macros = []
        for raw in data.get("macros", []) or []:
            if not isinstance(raw, dict):
                continue

            macro = MacroGroup.from_json(raw)
            if not macro.title:
                macro.title = "Main"
            if not macro.name:
                macro.name = self.safe_name(macro.title)
            macro.variables = []
            macros.append(macro)

        return {
            "name": self.safe_name(
                data.get("name", "")
                or data.get("title", "")
                or "untitled_project"
            ),
            "title": str(
                data.get("title", "") or "Untitled Project"
            ).strip()
            or "Untitled Project",
            "variables": self.normalize_variables(
                data.get("variables", []) or []
            ),
            "execution": MacroProject.normalize_execution(
                data.get("execution")
            ),
            "macros": macros,
            "active_macro": str(
                data.get("active_macro", "") or ""
            ).strip(),
        }

    def empty_project(self):
        macro = MacroGroup(
            name="main",
            title="Main",
            items=[],
            variables=[],
        )
        return {
            "name": "untitled_project",
            "title": "Untitled Project",
            "variables": [],
            "execution": MacroProject.default_execution(),
            "macros": [macro],
            "active_macro": macro.name,
        }

    def normalize_variables(self, variables):
        result = []
        names = set()

        for variable in variables or []:
            if not isinstance(variable, dict):
                continue

            name = str(variable.get("name", "") or "").strip()
            if not name or name in names:
                continue

            result.append(
                {
                    "name": name,
                    "type": str(
                        variable.get("type", "auto") or "auto"
                    ).strip()
                    or "auto",
                    "value": variable.get("value", ""),
                }
            )
            names.add(name)

        return result

    def list_groups(self):
        result = []
        root = self.macros_dir()

        for path in sorted(root.glob("*.json")):
            group = self.load_group(path)
            if group.name or group.title or group.items:
                result.append((path, group))

        return result
