import re
import unicodedata

def normalize_name(value: str) -> str:
    value = (value or '').strip().lower()
    value = ''.join(c for c in unicodedata.normalize('NFKD', value) if not unicodedata.combining(c))
    value = value.replace('-', ' ').replace('_', ' ')
    value = re.sub(r'(?<=\d)\s*(l|lt|lts|litros?)\b', ' l', value)
    value = re.sub(r'(?<=\d)\s*(ml|g|kg|lb)\b', r' \1', value)
    value = re.sub(r'[^a-z0-9.]+', ' ', value)
    return re.sub(r'\s+', ' ', value).strip()
