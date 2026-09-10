"""Interface en ligne de commande minimale."""

import argparse
import sys
from pathlib import Path

from tp11_projet.stock.depot import DepotJSON, ProduitInconnu
from tp11_projet.stock.service import ServiceStock, StockInsuffisant


def construire_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="stock")
    parser.add_argument("--fichier", default="stock.json", help="fichier de données")
    sous = parser.add_subparsers(dest="commande", required=True)

    p_ajout = sous.add_parser("ajouter")
    p_ajout.add_argument("reference")
    p_ajout.add_argument("nom")
    p_ajout.add_argument("prix_ht", type=float)
    p_ajout.add_argument("--quantite", type=int, default=0)

    p_sortie = sous.add_parser("sortir")
    p_sortie.add_argument("reference")
    p_sortie.add_argument("quantite", type=int)

    sous.add_parser("lister")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = construire_parser().parse_args(argv)
    service = ServiceStock(DepotJSON(Path(args.fichier)))
    try:
        if args.commande == "ajouter":
            p = service.ajouter_produit(args.reference, args.nom, args.prix_ht, args.quantite)
            print(f"ajouté : {p.reference} ({p.quantite})")
        elif args.commande == "sortir":
            p = service.sortir_stock(args.reference, args.quantite)
            print(f"{p.reference} : reste {p.quantite}")
        elif args.commande == "lister":
            for p in service.depot.tous():
                print(f"{p.reference:10s} {p.nom:20s} {p.quantite:4d}  {p.prix_ht:8.2f} €")
    except (ValueError, StockInsuffisant, ProduitInconnu) as exc:
        print(f"erreur : {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
