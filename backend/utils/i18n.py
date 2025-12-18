import os
import json
from typing import Dict, Any, Optional
from pathlib import Path

# Base directory for backend translations
LOCALES_DIR = Path(__file__).parent.parent / "locales"

class BackendI18n:
    _instance = None
    _translations: Dict[str, Dict[str, str]] = {}
    _default_lang = "zh"

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(BackendI18n, cls).__new__(cls)
            cls._instance._load_translations()
        return cls._instance

    def _load_translations(self):
        if not LOCALES_DIR.exists():
            LOCALES_DIR.mkdir(parents=True, exist_ok=True)
        
        for lang_file in LOCALES_DIR.glob("*.json"):
            lang = lang_file.stem
            try:
                with open(lang_file, "r", encoding="utf-8") as f:
                    self._translations[lang] = json.load(f)
            except Exception as e:
                print(f"Error loading translation for {lang}: {e}")

    def t(self, key: str, lang: Optional[str] = None, **kwargs) -> str:
        lang = lang or self._default_lang
        
        # Fallback to default if lang doesn't exist
        if lang not in self._translations:
            lang = self._default_lang
            
        trans = self._translations.get(lang, {}).get(key, key)
        
        if kwargs:
            try:
                return trans.format(**kwargs)
            except KeyError:
                return trans
        return trans

# Singleton instance
i18n = BackendI18n()

def t(key: str, lang: Optional[str] = None, **kwargs) -> str:
    return i18n.t(key, lang, **kwargs)
