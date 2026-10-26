from dataclasses import asdict
from datetime import date
from pathlib import Path

import pytest

from corridas.sources import cbat
from corridas.sources import minhas_inscricoes as mi

FIX = Path(__file__).parent / "fixtures"


def read(name: str) -> str:
    return (FIX / name).read_text(encoding="utf-8")


# ---------- Minhas Inscrições: listing ----------
def test_listing_cards_are_parsed_and_broken_cards_skipped():
    cards = mi.parse_listing(read("minhas_inscricoes_listing.html"))
    assert len(cards) == 2
    first = cards[0]
    assert first.event_id == "1001"
    assert first.key == "11111111-aaaa-4bbb-8ccc-000000000001"
    assert first.name == "3ª Corrida Exemplo da Serra"
    assert first.event_date == date(2026, 11, 8)
    assert (first.city, first.uf) == ("São José dos Campos", "SP")
    assert first.kind == "CORRIDA DE RUA"


def test_listing_url_has_paging_and_start_date():
    url = mi.listing_url(3, date(2026, 10, 26))
    assert "pagina=3" in url and "PesquisaDataInicio=26%2F10%2F2026" in url


# ---------- Minhas Inscrições: event page -> numbers only ----------
@pytest.fixture
def event_text():
    return mi.page_text(read("minhas_inscricoes_event.html"))


def test_distances_drop_walks_and_keep_runs(event_text):
    assert mi.extract_distances(event_text) == [5.0, 10.0]


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("Meia Maratona de Exemplo 21km", [21.0, 21.0975]),
        ("percursos de 10K e 21,1 km", [10.0, 21.1]),
        ("Maratona 42 km e Meia-Maratona", [21.0975, 42.0, 42.195]),
        ("km 500 de festa", []),
    ],
)
def test_distance_patterns(text, expected):
    assert mi.extract_distances(text) == expected


def test_prices_ignore_small_fees_and_scripts(event_text):
    assert mi.extract_prices(event_text) == (57.5, 115.0)


def test_status_and_start_time(event_text):
    assert mi.extract_status(event_text) == "open"
    assert mi.extract_status("Inscrições encerradas") == "closed"
    assert mi.extract_status("LOTE ESGOTADO") == "sold_out"
    assert mi.extract_start_time(event_text) == "07:30"


def test_no_text_from_the_event_page_reaches_the_record(monkeypatch, tmp_path, event_text):
    """The page has a contact e-mail: nothing but numbers/flags may come out of it."""

    class FakeClient:
        def get(self, url):
            html = (
                read("minhas_inscricoes_listing.html")
                if "Filtro" in url and "pagina=1&" in url
                else ("" if "Filtro" in url else read("minhas_inscricoes_event.html"))
            )
            return type("R", (), {"status": 200, "text": html})()

        def resolve_redirect(self, url):
            return "/Evento/CORRIDAEXEMPLO"

    source = mi.MinhasInscricoesSource(FakeClient(), tmp_path / "urls.json", today=date(2026, 10, 26))
    records = list(source.collect())
    assert len(records) == 1  # the PR event and the virtual one are filtered out
    flat = " ".join(str(v) for v in asdict(records[0]).values())
    assert "@" not in flat and "contato" not in flat
    assert records[0].source_url == "https://www.minhasinscricoes.com.br/Evento/CORRIDAEXEMPLO"


# ---------- CBAt ----------
def test_cbat_reads_the_header_only():
    rec = cbat.parse_event(read("cbat_event.html"), "https://cbat.org.br/evento/99999/maratona-exemplo")
    assert rec.event_date == date(2027, 7, 26)
    assert (rec.city, rec.uf) == ("São Paulo", "SP")
    assert rec.name == "Maratona Exemplo de São Paulo"
    assert rec.source_event_id == "99999"
    assert "Fulano" not in " ".join(str(v) for v in asdict(rec).values())


def test_cbat_sitemap_allow_list():
    xml = """<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
      <url><loc>https://cbat.org.br/evento/1/maratona-x</loc></url>
      <url><loc>https://cbat.org.br/resultados/1</loc></url>
      <url><loc>https://cbat.org.br/evento/2/meia/atletas</loc></url></urlset>"""
    assert cbat.event_urls(xml, r"^https://cbat\.org\.br/evento/\d+/[\w-]+$") == ["https://cbat.org.br/evento/1/maratona-x"]


def test_cbat_page_without_header_returns_none():
    assert cbat.parse_event("<html><body>layout novo</body></html>", "https://cbat.org.br/evento/1/x") is None
