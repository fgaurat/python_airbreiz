import pytest


class JournalEspion:
    """Un faux journal qui se contente de retenir ce qu'on lui dit."""

    def __init__(self):
        self.messages = []

    def noter(self, message):
        self.messages.append(message)


@pytest.fixture
def journal():
    return JournalEspion()


@pytest.fixture
def source(tmp_path):
    chemin = tmp_path / "todos.csv"
    chemin.write_text(
        "id,title,completed\n"
        "1,Relire le rapport,0\n"
        "2,Envoyer le compte rendu,1\n"
        "3,Appeler le client,0\n",
        encoding="utf-8",
    )
    return chemin
