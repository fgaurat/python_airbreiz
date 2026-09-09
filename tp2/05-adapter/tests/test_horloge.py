from unittest.mock import MagicMock, patch

import pytest

from horloges import HeureIndisponible, HorlogeSysteme, HorlogeTimeApi


def reponse_http(corps: bytes):
    """Imite ce que urlopen renvoie : un context manager avec read()."""
    reponse = MagicMock()
    reponse.read.return_value = corps
    reponse.__enter__.return_value = reponse
    return reponse


def test_timeapi_extrait_l_heure():
    corps = b'{"hour": 14, "minute": 32, "dateTime": "2026-09-08T14:32:07"}'
    with patch("horloges.urlopen", return_value=reponse_http(corps)) as urlopen:
        assert HorlogeTimeApi().heure() == 14
    urlopen.assert_called_once_with(HorlogeTimeApi.URL, timeout=5)


@pytest.mark.parametrize(
    "corps",
    [
        pytest.param(b"{}", id="cle_absente"),
        pytest.param(b"pas du json", id="json_invalide"),
        pytest.param(b'{"hour": "bizarre"}', id="heure_illisible"),
    ],
)
def test_timeapi_reponse_inexploitable(corps):
    with patch("horloges.urlopen", return_value=reponse_http(corps)):
        with pytest.raises(HeureIndisponible):
            HorlogeTimeApi().heure()


def test_timeapi_reseau_indisponible():
    with patch("horloges.urlopen", side_effect=OSError("pas de réseau")):
        with pytest.raises(HeureIndisponible):
            HorlogeTimeApi().heure()


def test_horloge_systeme_rend_une_heure_valide():
    assert 0 <= HorlogeSysteme().heure() <= 23
