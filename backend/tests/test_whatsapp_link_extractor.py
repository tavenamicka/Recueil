"""Tests de caractérisation pour whatsapp_link_extractor.py.

Le module est réutilisé tel quel pour le parsing (`parse_export`,
`fetch_title`) : ces tests documentent et verrouillent son comportement réel, y compris
ses aspérités connues (ex: le titre_brut imparfait quand plusieurs liens partagent une
même ligne), plutôt que de le corriger.

`categorize()` en revanche a été volontairement réécrit (classement par thème du
contenu — cuisine, bricolage, dessin... — plutôt que par plateforme d'origine) :
ses tests vérifient le nouveau comportement voulu, pas un comportement hérité.
"""

from unittest.mock import Mock, patch

import pytest

from app.services.whatsapp_link_extractor import categorize, fetch_og_image, fetch_title, parse_export

AUTEUR = "mickael tavenart"


def write_export(tmp_path, lines):
    path = tmp_path / "export.txt"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


class TestParseExport:
    def test_lien_avec_titre(self, tmp_path):
        path = write_export(
            tmp_path,
            [f"01/03/2026, 09:15 - {AUTEUR}: Regarde ce truc https://www.youtube.com/watch?v=abc123"],
        )
        records = parse_export(path)

        assert len(records) == 1
        record = records[0]
        assert record["date"] == "01/03/2026"
        assert record["time"] == "09:15"
        assert record["domain"] == "youtube.com"
        assert record["title_brut"] == "Regarde ce truc"
        assert record["url"] == "https://www.youtube.com/watch?v=abc123"

    def test_lien_sans_titre(self, tmp_path):
        path = write_export(tmp_path, [f"01/03/2026, 09:16 - {AUTEUR}: https://www.facebook.com/share/xyz"])
        records = parse_export(path)

        assert len(records) == 1
        assert records[0]["title_brut"] == ""
        assert records[0]["domain"] == "facebook.com"

    def test_plusieurs_liens_dans_le_meme_message(self, tmp_path):
        path = write_export(
            tmp_path,
            [f"01/03/2026, 09:17 - {AUTEUR}: Un lien https://a.example.com puis https://b.example.com"],
        )
        records = parse_export(path)

        assert len(records) == 2
        assert records[0]["url"] == "https://a.example.com"
        assert records[0]["title_brut"] == "Un lien"
        # Comportement réel (non corrigé) : le titre_brut du 2e lien inclut le 1er lien,
        # car le script coupe sur le texte brut sans tenir compte des liens déjà extraits.
        assert records[1]["url"] == "https://b.example.com"
        assert records[1]["title_brut"] == "Un lien https://a.example.com puis"

    def test_ligne_ignoree_si_auteur_different(self, tmp_path):
        path = write_export(tmp_path, ["01/03/2026, 09:18 - quelqu'un d'autre: https://ignored.example.com"])
        assert parse_export(path) == []

    def test_ligne_ignoree_si_date_malformee(self, tmp_path):
        path = write_export(tmp_path, [f"1/03/2026, 09:18 - {AUTEUR}: https://ignored.example.com"])
        assert parse_export(path) == []

    def test_parenthese_finale_retiree_de_lurl(self, tmp_path):
        path = write_export(tmp_path, [f"01/03/2026, 09:19 - {AUTEUR}: Vu ici (https://example.com/article)"])
        records = parse_export(path)

        assert len(records) == 1
        assert records[0]["url"] == "https://example.com/article"
        assert records[0]["domain"] == "example.com"

    def test_www_retire_du_domaine(self, tmp_path):
        path = write_export(tmp_path, [f"01/03/2026, 09:20 - {AUTEUR}: https://www.korben.info/article"])
        records = parse_export(path)
        assert records[0]["domain"] == "korben.info"


class TestCategorize:
    @pytest.mark.parametrize(
        "domain, expected",
        [
            ("amazon.fr", "Achats / Bons plans"),
            ("korben.info", "Technologie / IA"),
            ("numerama.com", "Technologie / IA"),
            ("clubic.com", "Technologie / IA"),
            ("romhustler.org", "Technologie / IA"),
            # facebook.com/youtube.com/instagram.com/linkedin.com n'impliquent plus aucun
            # thème : ce sont des plateformes génériques qui hébergent n'importe quel sujet
            # selon qui poste (le feed LinkedIn réel de l'utilisateur est majoritairement tech).
            ("facebook.com", "Autre"),
            ("youtube.com", "Autre"),
            ("instagram.com", "Autre"),
            ("linkedin.com", "Autre"),
            ("exemple-inconnu.tld", "Autre"),
        ],
    )
    def test_categorisation_par_domaine(self, domain, expected):
        assert categorize(domain, "un titre quelconque") == expected

    @pytest.mark.parametrize(
        "titre, expected",
        [
            ("Comment installer Docker", "Technologie / IA"),
            ("Une intelligence artificielle qui code", "Technologie / IA"),
            ("Astuces pour le jardin ce printemps", "Bricolage / Jardinage"),
            ("Stratégie marketing pour son entreprise", "Business / Marketing / Carrière"),
            ("Ma recette des nuggets de poulet", "Cuisine / Recettes"),
            ("Leçon de dessin manga pour débutants", "Dessin / Créativité manuelle"),
            ("No Back Pain Tonight avec cette routine fitness", "Sport / Santé / Bien-être"),
            ("5 phénomènes quantiques incroyables", "Sciences / Curiosités"),
            ("Song with just 4 chords à la guitare", "Musique"),
            ("Ces sites pour apprendre l'anglais gratuitement", "Langues / Apprentissage"),
            ("Une vidéo humour à mourir de rire", "Humour / Divertissement"),
        ],
    )
    def test_categorisation_par_mot_cle_du_titre(self, titre, expected):
        assert categorize("domaine-neutre.tld", titre) == expected

    def test_categorisation_insensible_a_la_casse(self):
        assert categorize("KORBEN.INFO", "PEU IMPORTE") == "Technologie / IA"

    def test_categorie_par_defaut(self):
        assert categorize("rien-de-connu.tld", "un titre sans mot-clé particulier") == "Autre"


class TestFetchTitle:
    @patch("app.services.whatsapp_link_extractor.requests.get")
    def test_utilise_og_title_si_present(self, mock_get):
        mock_get.return_value = Mock(
            text='<html><head><meta property="og:title" content="Titre Open Graph"></head></html>'
        )
        assert fetch_title("https://example.com") == "Titre Open Graph"

    @patch("app.services.whatsapp_link_extractor.requests.get")
    def test_repli_sur_title_html_si_pas_dog_title(self, mock_get):
        mock_get.return_value = Mock(text="<html><head><title>Titre HTML</title></head></html>")
        assert fetch_title("https://example.com") == "Titre HTML"

    @patch("app.services.whatsapp_link_extractor.requests.get")
    def test_chaine_vide_si_echec_reseau(self, mock_get):
        mock_get.side_effect = Exception("timeout")
        assert fetch_title("https://example.com") == ""


class TestFetchOgImage:
    @patch("app.services.whatsapp_link_extractor.requests.get")
    def test_utilise_og_image_si_present(self, mock_get):
        mock_get.return_value = Mock(
            text='<html><head><meta property="og:image" content="https://example.com/photo.jpg"></head></html>'
        )
        assert fetch_og_image("https://example.com") == "https://example.com/photo.jpg"

    @patch("app.services.whatsapp_link_extractor.requests.get")
    def test_chaine_vide_si_pas_dog_image(self, mock_get):
        mock_get.return_value = Mock(text="<html><head><title>Sans image</title></head></html>")
        assert fetch_og_image("https://example.com") == ""

    @patch("app.services.whatsapp_link_extractor.requests.get")
    def test_chaine_vide_si_echec_reseau(self, mock_get):
        mock_get.side_effect = Exception("timeout")
        assert fetch_og_image("https://example.com") == ""
