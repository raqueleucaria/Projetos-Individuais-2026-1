"""Hash SHA-256 do conteúdo do PDF — ver ADR-0003 (idempotência)."""

import hashlib
from pathlib import Path


def hash_arquivo(caminho: Path | str) -> str:
    sha256 = hashlib.sha256()
    with open(caminho, "rb") as f:
        for bloco in iter(lambda: f.read(8192), b""):
            sha256.update(bloco)
    return sha256.hexdigest()
