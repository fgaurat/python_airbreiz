"""Code métier du TP07 : envoi de notifications par email.

Deux dépendances externes :
  - EmailClient  : parle SMTP (smtplib) -> impossible en test
  - AnnuaireClient : appelle une API HTTP pour trouver l'email d'un utilisateur

ServiceNotification reçoit ces deux dépendances par INJECTION (constructeur) :
c'est ce qui rend le service facile à tester avec des doublures.
"""

import json
import logging
import smtplib
import urllib.request
from email.message import EmailMessage

logger = logging.getLogger(__name__)


class EmailClient:
    def __init__(self, hote: str, port: int = 25):
        self.hote = hote
        self.port = port

    def envoyer(self, destinataire: str, sujet: str, corps: str) -> None:
        message = EmailMessage()
        message["To"] = destinataire
        message["Subject"] = sujet
        message.set_content(corps)
        with smtplib.SMTP(self.hote, self.port) as smtp:
            smtp.send_message(message)


class AnnuaireClient:
    def __init__(self, url_base: str):
        self.url_base = url_base

    def email_de(self, utilisateur: str) -> str | None:
        with urllib.request.urlopen(f"{self.url_base}/utilisateurs/{utilisateur}") as rep:
            return json.loads(rep.read()).get("email")


class ServiceNotification:
    def __init__(self, email_client: EmailClient, annuaire: AnnuaireClient):
        self.email_client = email_client
        self.annuaire = annuaire

    def notifier(self, utilisateur: str, message: str) -> bool:
        email = self.annuaire.email_de(utilisateur)
        if not email:
            logger.warning("aucun email pour %s", utilisateur)
            return False
        self.email_client.envoyer(email, "Notification", message)
        return True

    def notifier_tous(self, utilisateurs: list[str], message: str) -> int:
        """Notifie chaque utilisateur ; continue même si un envoi échoue."""
        envoyes = 0
        for utilisateur in utilisateurs:
            try:
                if self.notifier(utilisateur, message):
                    envoyes += 1
            except Exception:
                logger.exception("échec pour %s", utilisateur)
        return envoyes
