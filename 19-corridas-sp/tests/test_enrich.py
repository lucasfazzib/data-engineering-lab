from corridas.enrich import build, ring_centroid


def test_square_centroid():
    lon, lat = ring_centroid([[0, 0], [2, 0], [2, 2], [0, 2], [0, 0]])
    assert (round(lon, 6), round(lat, 6)) == (1, 1)


def test_build_joins_names_and_centroids():
    localidades = [{"id": 3550308, "nome": "São Paulo"}, {"id": 1, "nome": "Sem malha"}]
    malhas = {
        "features": [
            {
                "properties": {"codarea": "3550308"},
                "geometry": {"type": "Polygon", "coordinates": [[[0, 0], [2, 0], [2, 2], [0, 2], [0, 0]]]},
            }
        ]
    }
    rows = build(localidades, malhas)
    assert rows[0] == {"ibge_code": "3550308", "name": "São Paulo", "uf": "SP", "lat": 1.0, "lon": 1.0}
    assert rows[1]["lat"] is None
