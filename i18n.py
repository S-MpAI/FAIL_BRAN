import json
import os

LANG_FILE = os.path.join(os.path.dirname(__file__), "locales", "lang.json")
LOCALES_DIR = os.path.join(os.path.dirname(__file__), "locales")
DEFAULT_LANG = "en"


class I18N:
    def __init__(self, lang):
        self.lang = DEFAULT_LANG
        self.translations = {}
        self.load_lang(lang)

    def load_lang(self, lang):
        path = os.path.join(LOCALES_DIR, f"{lang}.json")

        if not os.path.isfile(path):
            raise ValueError(f"Locale '{lang}' not found")

        with open(path, "r", encoding="utf-8") as f:
            self.translations = json.load(f)

        self.lang = lang

    def t(self, key, **kwargs):
        text = self.translations.get(key, key)
        try:
            return text.format(**kwargs)
        except Exception:
            return text


def ensure_lang_file():
    if not os.path.exists(LANG_FILE):
        with open(LANG_FILE, "w", encoding="utf-8") as f:
            json.dump({"value": DEFAULT_LANG}, f, indent=2)
        return DEFAULT_LANG, None

    try:
        with open(LANG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        lang = data.get("value", DEFAULT_LANG)

        locale_path = os.path.join(LOCALES_DIR, f"{lang}.json")
        if not os.path.isfile(locale_path):
            error = f"[i18n] Unsupported language '{lang}', fallback to '{DEFAULT_LANG}'"
            print(error)
            return DEFAULT_LANG, error

        return lang, None

    except Exception as e:
        error = f"[i18n] Failed to read lang.json ({e}), fallback to '{DEFAULT_LANG}'"
        print(error)
        return DEFAULT_LANG, error
