import json
from pathlib import Path
from typing import Dict


def load_locales(path: str = 'bot/locales') -> Dict[str, Dict[str, str]]:
    data: Dict[str, Dict[str, str]] = {}
    for file in Path(path).glob('*.json'):
        data[file.stem] = json.loads(file.read_text())
    return data


LOCALES = load_locales()


def t(lang: str, key: str) -> str:
    default = LOCALES.get('ru', {})
    return LOCALES.get(lang, default).get(key, default.get(key, key))
