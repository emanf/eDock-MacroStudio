VARIABLE_FIELD_TYPES = {"variable"}
COMMENT_FIELD_TYPES = {"comment"}
MACRO_GROUP_FIELD_TYPES = {"macro_group"}


def reference_field_names(registry, item, value_types):
    command = registry.get(getattr(item, "command_id", ""))
    if command is None:
        return []

    names = []
    for field in getattr(command, "fields", None) or []:
        if not isinstance(field, dict):
            continue

        value_type = str(field.get("value_type", "") or "").strip().lower()
        if value_type in value_types:
            field_name = str(field.get("name", "") or "").strip()
            if field_name:
                names.append(field_name)

    return names


def rename_variable_in_items(items, registry, old_name, new_name):
    old_name = str(old_name or "").strip()
    new_name = str(new_name or "").strip()
    if not old_name or not new_name or old_name == new_name:
        return 0

    prefix = old_name + "."
    count = 0

    for item in items or []:
        values = getattr(item, "values", None)
        if not isinstance(values, dict):
            continue

        for field_name in reference_field_names(registry, item, VARIABLE_FIELD_TYPES):
            value = str(values.get(field_name, "") or "").strip()
            if not value:
                continue

            if value == old_name:
                values[field_name] = new_name
                count += 1
            elif value.startswith(prefix):
                values[field_name] = new_name + value[len(old_name):]
                count += 1

    return count


def rename_variable_references(macros, registry, old_name, new_name):
    count = 0
    for macro in macros or []:
        count += rename_variable_in_items(getattr(macro, "items", None), registry, old_name, new_name)
    return count


def rename_comment_references(items, registry, old_name, new_name):
    old_name = str(old_name or "").strip()
    new_name = str(new_name or "").strip()
    if not old_name or not new_name or old_name == new_name:
        return 0

    count = 0

    for item in items or []:
        values = getattr(item, "values", None)
        if not isinstance(values, dict):
            continue

        for field_name in reference_field_names(registry, item, COMMENT_FIELD_TYPES):
            value = str(values.get(field_name, "") or "").strip()
            if value == old_name:
                values[field_name] = new_name
                count += 1

    return count


def rename_macro_group_references(macros, registry, old_name, new_name, old_title=None, new_title=None):
    old_name = str(old_name or "").strip()
    new_name = str(new_name or "").strip()
    old_title = str(old_title or "").strip()
    new_title = str(new_title or "").strip()

    if not old_name or not new_name:
        return 0
    
    count = 0

    for macro in macros or []:
        for item in getattr(macro, "items", None) or []:
            values = getattr(item, "values", None)
            if not isinstance(values, dict):
                continue

            for field_name in reference_field_names(registry, item, MACRO_GROUP_FIELD_TYPES):
                stored = values.get(field_name, "")
                changed = False

                if isinstance(stored, dict):
                    stored_value = str(stored.get("value", "") or "").strip()
                    stored_title = str(stored.get("title", "") or "").strip()

                    if stored_value == old_name and (not old_title or stored_title == old_title):
                        stored["value"] = new_name
                        stored["title"] = new_title
                        changed = True
                
                else:
                    value = str(stored or "").strip()
                    if value == old_name or (old_title and value == old_title):
                        values[field_name] = {
                            "title": new_title,
                            "value": new_name
                        }
                        changed = True

                if changed:
                    count += 1

    return count
