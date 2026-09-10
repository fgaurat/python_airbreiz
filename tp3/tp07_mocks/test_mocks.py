"""TP07 - Doublures de test : unittest.mock et pytest-mock.

Vocabulaire (Gerard Meszaros) :
  - Dummy : objet passé mais jamais utilisé.
  - Stub  : renvoie des réponses préparées (return_value).
  - Fake  : implémentation simplifiée mais fonctionnelle (ex. FakeEmailClient).
  - Spy   : enregistre les appels tout en appelant le vrai code (mocker.spy).
  - Mock  : enregistre les appels ET permet de vérifier qu'ils ont eu lieu.

`unittest.mock` (stdlib) fournit Mock / MagicMock / patch.
`pytest-mock` ajoute la fixture `mocker` : mêmes objets, nettoyage automatique.
"""

from unittest.mock import MagicMock, Mock, call, create_autospec, patch

import pytest

from tp07_mocks import notifications
from tp07_mocks.notifications import AnnuaireClient, EmailClient, ServiceNotification

# ---------------------------------------------------------------------------
# 1. Mock de base : return_value + assertions sur les appels
# ---------------------------------------------------------------------------


def test_notifier_envoie_un_email():
    annuaire = Mock()
    annuaire.email_de.return_value = "alice@example.com"  # stub
    email_client = Mock()

    service = ServiceNotification(email_client, annuaire)
    assert service.notifier("alice", "Bonjour !") is True

    annuaire.email_de.assert_called_once_with("alice")
    email_client.envoyer.assert_called_once_with("alice@example.com", "Notification", "Bonjour !")


def test_notifier_utilisateur_sans_email():
    annuaire = Mock()
    annuaire.email_de.return_value = None
    email_client = Mock()

    service = ServiceNotification(email_client, annuaire)
    assert service.notifier("inconnu", "...") is False

    email_client.envoyer.assert_not_called()


# ---------------------------------------------------------------------------
# 2. Inspecter les appels : call_args, call_count, call_args_list
# ---------------------------------------------------------------------------


def test_notifier_tous_inspecte_les_appels():
    annuaire = Mock()
    annuaire.email_de.side_effect = lambda u: f"{u}@example.com"  # fonction
    email_client = Mock()

    service = ServiceNotification(email_client, annuaire)
    assert service.notifier_tous(["a", "b", "c"], "msg") == 3

    assert email_client.envoyer.call_count == 3
    assert email_client.envoyer.call_args_list == [
        call("a@example.com", "Notification", "msg"),
        call("b@example.com", "Notification", "msg"),
        call("c@example.com", "Notification", "msg"),
    ]
    # Dernier appel : .args et .kwargs
    assert email_client.envoyer.call_args.args[0] == "c@example.com"
    annuaire.email_de.assert_any_call("b")


# ---------------------------------------------------------------------------
# 3. side_effect : exception, ou séquence de valeurs
# ---------------------------------------------------------------------------


def test_side_effect_exception():
    annuaire = Mock()
    annuaire.email_de.return_value = "x@example.com"
    email_client = Mock()
    email_client.envoyer.side_effect = ConnectionError("SMTP injoignable")

    service = ServiceNotification(email_client, annuaire)
    # notifier() propage l'exception...
    with pytest.raises(ConnectionError):
        service.notifier("x", "m")
    # ...mais notifier_tous() la journalise et continue
    assert service.notifier_tous(["x", "y"], "m") == 0


def test_side_effect_sequence():
    annuaire = Mock()
    annuaire.email_de.side_effect = ["a@ex.com", None, "c@ex.com"]  # itérable
    email_client = Mock()

    service = ServiceNotification(email_client, annuaire)
    assert service.notifier_tous(["a", "b", "c"], "m") == 2


# ---------------------------------------------------------------------------
# 4. spec / autospec : un mock qui respecte l'interface réelle
# ---------------------------------------------------------------------------


def test_mock_sans_spec_accepte_n_importe_quoi():
    m = Mock()
    m.methode_qui_n_existe_pas()  # aucun problème : dangereux !
    assert m.methode_qui_n_existe_pas.called


def test_mock_avec_spec_refuse_les_attributs_inconnus():
    m = Mock(spec=EmailClient)
    m.envoyer("a", "b", "c")
    with pytest.raises(AttributeError):
        m.envoyerr("a", "b", "c")  # faute de frappe détectée


def test_autospec_verifie_aussi_la_signature():
    m = create_autospec(EmailClient, instance=True)
    m.envoyer("a", "b", "c")
    with pytest.raises(TypeError):
        m.envoyer("un seul argument")  # signature vérifiée


# ---------------------------------------------------------------------------
# 5. patch : remplacer un objet là où il est utilisé
# ---------------------------------------------------------------------------


@patch("tp07_mocks.notifications.smtplib.SMTP")  # décorateur -> injecté en paramètre
def test_email_client_avec_patch_decorateur(smtp_mock):
    client = EmailClient("smtp.example.com", 587)
    client.envoyer("bob@example.com", "Sujet", "Corps")

    smtp_mock.assert_called_once_with("smtp.example.com", 587)
    # `with smtplib.SMTP(...) as smtp` -> l'objet utilisé est __enter__()
    instance = smtp_mock.return_value.__enter__.return_value
    instance.send_message.assert_called_once()
    message = instance.send_message.call_args.args[0]
    assert message["To"] == "bob@example.com"
    assert message["Subject"] == "Sujet"


def test_email_client_avec_patch_contexte():
    with patch("tp07_mocks.notifications.smtplib.SMTP") as smtp_mock:
        EmailClient("h").envoyer("d", "s", "c")
        assert smtp_mock.called
    # Hors du bloc `with`, smtplib.SMTP est restauré
    assert notifications.smtplib.SMTP is not smtp_mock


def test_patch_object():
    # patch.object(cible, "attribut") : plus lisible quand on a déjà l'objet
    with patch.object(AnnuaireClient, "email_de", return_value="z@ex.com") as m:
        assert AnnuaireClient("http://x").email_de("z") == "z@ex.com"
        m.assert_called_once_with("z")


# ---------------------------------------------------------------------------
# 6. MagicMock : supporte les méthodes spéciales (__len__, __iter__, __enter__...)
# ---------------------------------------------------------------------------


def test_magicmock():
    m = MagicMock()
    m.__len__.return_value = 3
    m.__iter__.return_value = iter([1, 2, 3])
    assert len(m) == 3
    assert list(m) == [1, 2, 3]
    with m as ctx:  # __enter__ / __exit__ existent aussi
        assert ctx is m.__enter__.return_value


# ---------------------------------------------------------------------------
# 7. pytest-mock : la fixture `mocker`
# ---------------------------------------------------------------------------


def test_mocker_patch(mocker):
    # Équivalent de @patch, mais annulé automatiquement à la fin du test,
    # sans décorateur ni bloc `with`, et compatible avec les autres fixtures.
    smtp_mock = mocker.patch("tp07_mocks.notifications.smtplib.SMTP")
    EmailClient("h").envoyer("d", "s", "c")
    smtp_mock.assert_called_once_with("h", 25)


def test_mocker_patch_object(mocker):
    mocker.patch.object(AnnuaireClient, "email_de", return_value=None)
    service = ServiceNotification(mocker.Mock(), AnnuaireClient("http://x"))
    assert service.notifier("u", "m") is False


def test_mocker_spy(mocker):
    """Un spy appelle la VRAIE méthode mais enregistre les appels."""

    class AnnuaireMemoire:
        def email_de(self, utilisateur):
            return f"{utilisateur}@memoire.local"

    annuaire = AnnuaireMemoire()
    spy = mocker.spy(annuaire, "email_de")

    service = ServiceNotification(mocker.Mock(), annuaire)
    service.notifier("eve", "m")

    spy.assert_called_once_with("eve")
    assert spy.spy_return == "eve@memoire.local"


# ---------------------------------------------------------------------------
# 8. Fake : parfois plus simple et plus lisible qu'un mock
# ---------------------------------------------------------------------------


class FakeEmailClient:
    """Implémentation en mémoire : garde les emails dans une liste."""

    def __init__(self):
        self.boite_envoi: list[tuple[str, str, str]] = []

    def envoyer(self, destinataire, sujet, corps):
        self.boite_envoi.append((destinataire, sujet, corps))


class FakeAnnuaire:
    def __init__(self, **emails):
        self._emails = emails

    def email_de(self, utilisateur):
        return self._emails.get(utilisateur)


@pytest.fixture
def service_fake():
    email_client = FakeEmailClient()
    annuaire = FakeAnnuaire(alice="alice@ex.com", bob="bob@ex.com")
    return ServiceNotification(email_client, annuaire), email_client


def test_avec_fakes(service_fake):
    service, email_client = service_fake
    assert service.notifier_tous(["alice", "bob", "carol"], "réunion à 10h") == 2
    assert email_client.boite_envoi == [
        ("alice@ex.com", "Notification", "réunion à 10h"),
        ("bob@ex.com", "Notification", "réunion à 10h"),
    ]


# ---------------------------------------------------------------------------
# 9. Vérifier les logs produits en cas d'erreur (aperçu de caplog, TP08)
# ---------------------------------------------------------------------------


def test_erreur_journalisee(caplog):
    annuaire = Mock()
    annuaire.email_de.return_value = "x@ex.com"
    email_client = Mock()
    email_client.envoyer.side_effect = RuntimeError("boum")

    ServiceNotification(email_client, annuaire).notifier_tous(["x"], "m")

    assert "échec pour x" in caplog.text
    assert caplog.records[0].levelname == "ERROR"
