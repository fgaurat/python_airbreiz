
def bonjour(nom: str | None = None) -> str:
    """Retourne une salutation, avec le nom si fourni."""
    if nom is None:
        return "Bonjour"
    return f"Bonjour {nom}"
