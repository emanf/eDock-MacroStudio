from core.rendering.material_icons import MaterialIcons


class MacroCommandCategory:
    def __init__(self, category_id: str, title: str, icon: str):
        self.id = str(category_id or "").strip()
        self.title = str(title or "").strip()
        self.icon = str(icon or "").strip()

    def normalized_id(self):
        return self.id.strip().lower()

    def get_glyph(self) -> str:
        return MaterialIcons.glyph(self.icon, "")


class CategoryRegistry:
    def __init__(self):
        self._categories = {}

    def register(self, category: MacroCommandCategory):
        if not isinstance(category, MacroCommandCategory):
            return None

        category_id = category.normalized_id()
        if not category_id:
            return None

        if category_id not in self._categories:
            title = category.title or category.id or "Other"
            icon = category.icon or "m:extension"
            self._categories[category_id] = MacroCommandCategory(category_id, title, icon)

        return self._categories[category_id]

    def get(self, category_id: str) -> MacroCommandCategory:
        cat_id_lower = str(category_id or "").strip().lower()
        if cat_id_lower in self._categories:
            return self._categories[cat_id_lower]
        fallback_title = str(category_id or "Other").strip() or "Other"
        return MacroCommandCategory(cat_id_lower, fallback_title, "m:extension")

    def has(self, category_id: str):
        cat_id_lower = str(category_id or "").strip().lower()
        return cat_id_lower in self._categories

    def get_all(self):
        return list(self._categories.values())
