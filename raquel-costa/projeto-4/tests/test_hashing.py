import hashlib

from uda.hashing import hash_arquivo


def test_hash_arquivo_eh_sha256(tmp_path):
    arquivo = tmp_path / "exemplo.pdf"
    conteudo = b"conteudo de exemplo do pdf"
    arquivo.write_bytes(conteudo)

    esperado = hashlib.sha256(conteudo).hexdigest()
    assert hash_arquivo(arquivo) == esperado


def test_hash_arquivo_deterministico(tmp_path):
    arquivo = tmp_path / "exemplo.pdf"
    arquivo.write_bytes(b"abc")

    assert hash_arquivo(arquivo) == hash_arquivo(arquivo)
