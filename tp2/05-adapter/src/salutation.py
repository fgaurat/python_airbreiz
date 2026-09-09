from horloges import Horloge


def formule(heure: int) -> str:
    if not 0 <= heure <= 23:
        raise ValueError(f"heure invalide : {heure}")
    if heure < 12:
        return "Bonjour"
    if heure < 18:
        return "Bon après-midi"
    return "Bonsoir"


def saluer(nom: str, horloge: Horloge) -> str:
    return f"{formule(horloge.heure())}, {nom} !"
