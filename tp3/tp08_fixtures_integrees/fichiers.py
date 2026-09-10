"""Code métier du TP08 : fichiers, sortie standard, logs, avertissements."""

import csv
import logging
import sys
import warnings
from pathlib import Path

logger = logging.getLogger("fichiers")


def ecrire_csv(chemin: Path, lignes: list[dict]) -> None:
    if not lignes:
        raise ValueError("rien à écrire")
    with open(chemin, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(lignes[0].keys()))
        writer.writeheader()
        writer.writerows(lignes)
    logger.info("%d lignes écrites dans %s", len(lignes), chemin.name)


def lire_csv(chemin: Path) -> list[dict]:
    with open(chemin, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def compter_lignes(chemin: Path) -> int:
    return len(chemin.read_text(encoding="utf-8").splitlines())


def afficher_rapport(lignes: list[dict]) -> None:
    print(f"Rapport : {len(lignes)} enregistrement(s)")
    for ligne in lignes:
        print(" - " + ", ".join(f"{k}={v}" for k, v in ligne.items()))
    if not lignes:
        print("attention : rapport vide", file=sys.stderr)


def traiter(chemin: Path) -> int:
    logger.debug("début du traitement de %s", chemin)
    if not chemin.exists():
        logger.error("fichier introuvable : %s", chemin)
        return 0
    n = compter_lignes(chemin)
    if n > 1000:
        logger.warning("fichier volumineux (%d lignes)", n)
    logger.info("traitement terminé : %d lignes", n)
    return n


def ancienne_fonction(x):
    warnings.warn("ancienne_fonction est obsolète, utilisez nouvelle_fonction", DeprecationWarning, stacklevel=2)
    return nouvelle_fonction(x)


def nouvelle_fonction(x):
    return x * 2
