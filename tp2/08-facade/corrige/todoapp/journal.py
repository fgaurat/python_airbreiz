class Journal:
    """Un journal minimal : affiche et garde les messages."""

    def __init__(self):
        self.messages: list[str] = []

    def noter(self, message: str) -> None:
        self.messages.append(message)
        print(f"[journal] {message}")
