"""Configuração centralizada do pipeline (env vars, paths)."""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent.parent

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")

DATA_DIR = BASE_DIR / "data"
DB_PATH = BASE_DIR / "catalogo.db"

# Palavras-chave do Pré-filtro de Páginas (ADR-0001)
PAGE_FILTER_KEYWORDS = [
    "lançamento",
    "lancamento",
    "venda",
    "vgv",
    "unidade",
]
