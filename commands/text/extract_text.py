import re

from ...core.model.macro_category import MacroCommandCategory
from ...core.model.macro_command import MacroCommand, ResultPolicy


TextCategory = MacroCommandCategory("text", "Text", "mc:e264")


REGEX_PATTERNS = {
    "emails": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
    "urls": r"\b(?:https?://|www\.)[^\s<>'\"]+",
    "image_urls": r"\b(?:https?://|www\.)[^\s<>'\"]+\.(?:png|jpe?g|gif|webp|svg|bmp|ico|tiff?)(?:\?[^\s<>'\"]*)?",
    "image_sources": r"<img\b[^>]*\bsrc=[\"']([^\"']+)[\"'][^>]*>",
    "html_links": r"<a\b[^>]*\bhref=[\"']([^\"']+)[\"'][^>]*>",
    "phone_numbers": r"(?<!\w)(?:\+?\d{1,3}[\s.-]?)?(?:\(?\d{2,4}\)?[\s.-]?)?\d{3,4}[\s.-]?\d{3,4}(?!\w)",
    "ipv4_addresses": r"\b(?:(?:25[0-5]|2[0-4]\d|1?\d?\d)\.){3}(?:25[0-5]|2[0-4]\d|1?\d?\d)\b",
    "ipv6_addresses": r"\b(?:[A-Fa-f0-9]{1,4}:){2,7}[A-Fa-f0-9]{1,4}\b",
    "dates": r"\b(?:\d{4}[-/]\d{1,2}[-/]\d{1,2}|\d{1,2}[-/]\d{1,2}[-/]\d{2,4})\b",
    "times": r"\b(?:[01]?\d|2[0-3]):[0-5]\d(?::[0-5]\d)?(?:\s?[APMapm]{2})?\b",
    "numbers": r"(?<!\w)[+-]?(?:\d+(?:\.\d+)?|\.\d+)(?!\w)",
    "integers": r"(?<![\w.])[+-]?\d+(?![\w.])",
    "decimal_numbers": r"(?<!\w)[+-]?(?:\d+\.\d+|\.\d+)(?!\w)",
    "hex_colors": r"(?<!\w)#(?:[A-Fa-f0-9]{3}|[A-Fa-f0-9]{6}|[A-Fa-f0-9]{8})\b",
    "hashtags": r"(?<!\w)#[A-Za-z0-9_]+",
    "mentions": r"(?<!\w)@[A-Za-z0-9_]+",
    "domain_names": r"\b(?:[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?\.)+[A-Za-z]{2,}\b",
    "uuid_values": r"\b[A-Fa-f0-9]{8}-[A-Fa-f0-9]{4}-[1-5][A-Fa-f0-9]{3}-[89ABab][A-Fa-f0-9]{3}-[A-Fa-f0-9]{12}\b",
    "mac_addresses": r"\b(?:[A-Fa-f0-9]{2}[:-]){5}[A-Fa-f0-9]{2}\b",
    "html_tags": r"</?[A-Za-z][A-Za-z0-9:-]*(?:\s[^<>]*)?>",
    "file_paths": r"(?:[A-Za-z]:\\(?:[^\\/:*?\"<>|\r\n]+\\)*[^\\/:*?\"<>|\r\n]*|/(?:[^/\0\r\n]+/)*[^/\0\r\n]*)",
    "file_names": r"\b[A-Za-z0-9._ -]+\.[A-Za-z0-9]{1,10}\b",
    "json_keys": r"[\"']([^\"']+)[\"']\s*:",
    "custom": "",
}


PATTERN_OPTIONS = [
    "emails",
    "urls",
    "image_urls",
    "image_sources",
    "html_links",
    "phone_numbers",
    "ipv4_addresses",
    "ipv6_addresses",
    "dates",
    "times",
    "numbers",
    "integers",
    "decimal_numbers",
    "hex_colors",
    "hashtags",
    "mentions",
    "domain_names",
    "uuid_values",
    "mac_addresses",
    "html_tags",
    "file_paths",
    "file_names",
    "json_keys",
    "custom",
]


def get_extract_pattern(values):
    pattern_type = values.get("pattern_type")
    if pattern_type == "custom":
        return str(values.get("custom_regex", "") or "")
    return REGEX_PATTERNS.get(pattern_type, "")


class ExtractTextCommand(MacroCommand):
    id = "text.extract"
    title = "Extract Text"
    category = TextCategory
    icon = "mc:e0ee"
    description = "Extract useful text patterns with regex."
    result_policy = ResultPolicy.VARIABLE
    fields = [
        {
            "name": "text_source",
            "title": "Text Source",
            "value_type": "choice",
            "options": ["value", "variable"],
            "default_value": "variable",
        },
        {
            "name": "text_value",
            "required": False,
            "title": "Text",
            "place_holder": "Paste text here",
            "value_type": "string",
            "default_value": "",
            "visible_if": {
                "field": "text_source",
                "operator": "==",
                "value": "value",
            },
        },
        {
            "name": "text_variable",
            "required": False,
            "title": "Text Variable",
            "place_holder": "text_value",
            "value_type": "variable",
            "default_value": "",
            "visible_if": {
                "field": "text_source",
                "operator": "==",
                "value": "variable",
            },
        },
        {
            "name": "pattern_type",
            "title": "Extract",
            "value_type": "choice",
            "options": PATTERN_OPTIONS,
            "default_value": "emails",
        },
        {
            "name": "custom_regex",
            "required": False,
            "title": "Custom Regex",
            "place_holder": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
            "value_type": "string",
            "default_value": "",
            "visible_if": {
                "field": "pattern_type",
                "operator": "==",
                "value": "custom",
            },
        },
        {
            "name": "case_sensitive",
            "title": "Case Sensitive",
            "value_type": "bool",
            "default_value": False,
        },
        {
            "name": "output_mode",
            "title": "Output",
            "value_type": "choice",
            "options": ["full_match", "first_group", "all_groups"],
            "default_value": "full_match",
        },
        {
            "name": "unique_only",
            "title": "Unique Only",
            "value_type": "bool",
            "default_value": False,
        },
        {
            "name": "max_results",
            "title": "Max Results",
            "place_holder": "0 means all",
            "value_type": "int",
            "default_value": 0,
            "required": False,
            "min_value": 0,
        },
        {
            "name": "target_variable",
            "title": "Save Result To",
            "place_holder": "extracted_text",
            "value_type": "variable",
            "default_value": "",
        },
    ]

    def display_text(self, values=None):
        values = self.normalize_values(values)
        target_variable = values.get("target_variable")
        pattern_type = values.get("pattern_type")
        return f"extract {pattern_type} -> {target_variable}"

    def execute(self, values=None, runtime=None):
        values = self.normalize_values(values)
        target_variable = values.get("target_variable")
        text_source = values.get("text_source")
        pattern = get_extract_pattern(values)
        case_sensitive = bool(values.get("case_sensitive", False))
        output_mode = values.get("output_mode") or "full_match"
        unique_only = bool(values.get("unique_only", False))
        max_results = int(values.get("max_results", 0) or 0)

        if text_source == "variable":
            text_value = runtime.vars.get(values.get("text_variable"))
        else:
            text_value = values.get("text_value")

        source_text = str("" if text_value is None else text_value)

        try:
            regex = re.compile(pattern, 0 if case_sensitive else re.IGNORECASE)
        except re.error as error:
            raise ValueError(f"Invalid regex pattern: {error}")

        result_items = []

        for match in regex.finditer(source_text):
            if output_mode == "first_group":
                if match.groups():
                    item = match.group(1)
                else:
                    item = match.group(0)
            elif output_mode == "all_groups":
                if match.groups():
                    item = list(match.groups())
                else:
                    item = [match.group(0)]
            else:
                item = match.group(0)

            if unique_only and item in result_items:
                continue

            result_items.append(item)

            if max_results > 0 and len(result_items) >= max_results:
                break

        runtime.vars.add(target_variable)
        variable_type = runtime.vars.type_of(target_variable)
        final_value = runtime.helper.convert_variable_value(result_items, variable_type)
        runtime.vars.set(target_variable, final_value)

        return {
            "variable_name": target_variable,
            "value": final_value,
        }


def register_macro(registry):
    registry.register(ExtractTextCommand)
