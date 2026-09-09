from pathlib import Path


def ecrire(chemin, texte: str) -> None:
    Path(chemin).write_text(texte, encoding="utf-8")
