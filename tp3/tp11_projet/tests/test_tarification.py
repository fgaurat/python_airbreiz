"""Tests du client HTTP : on patche urlopen (TP06 / TP07)."""

import io
import json
from contextlib import closing

import pytest

from tp11_projet.stock.tarification import ClientTaux, ServiceTauxIndisponible


def _reponse(donnees: dict):
    """Fabrique un objet qui imite la réponse d'urlopen (context manager + read)."""
    return closing(io.BytesIO(json.dumps(donnees).encode()))


def test_eur_sans_appel_reseau(mocker):
    urlopen = mocker.patch("tp11_projet.stock.tarification.urllib.request.urlopen")
    assert ClientTaux().taux("EUR") == 1.0
    urlopen.assert_not_called()


def test_taux_usd(mocker):
    urlopen = mocker.patch("tp11_projet.stock.tarification.urllib.request.urlopen")
    urlopen.return_value = _reponse({"rates": {"USD": 1.0837}})

    assert ClientTaux().taux("USD") == pytest.approx(1.0837)
    urlopen.assert_called_once_with("https://api.taux.example/latest?base=EUR&symbols=USD", timeout=3.0)


def test_erreur_reseau(mocker):
    mocker.patch("tp11_projet.stock.tarification.urllib.request.urlopen", side_effect=OSError("timeout"))
    with pytest.raises(ServiceTauxIndisponible, match="timeout"):
        ClientTaux().taux("USD")


@pytest.mark.parametrize("corps", [{}, {"rates": {}}, {"rates": {"USD": "abc"}}, {"rates": None}])
def test_reponse_invalide(mocker, corps):
    mocker.patch("tp11_projet.stock.tarification.urllib.request.urlopen", return_value=_reponse(corps))
    with pytest.raises(ServiceTauxIndisponible, match="réponse invalide"):
        ClientTaux().taux("USD")


def test_url_et_timeout_personnalises(mocker):
    urlopen = mocker.patch("tp11_projet.stock.tarification.urllib.request.urlopen", return_value=_reponse({"rates": {"GBP": 0.85}}))
    ClientTaux(url="http://local/taux", timeout=1).taux("GBP")
    assert urlopen.call_args.args[0].startswith("http://local/taux?")
    assert urlopen.call_args.kwargs["timeout"] == 1
