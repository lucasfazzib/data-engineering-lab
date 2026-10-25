"""A minimal TSE-shaped feed (same keys and number formats as the real file), built in code.

No real file is committed: fixtures stay small, readable, and free of anything but public-office names.
"""

import json


def _br(n: float, decimals: int = 2) -> str:
    return f"{n:.{decimals}f}".replace(".", ",")


def feed_json(scope: str, time: str, pct_counted: float, lula: int, flavio: int, *, final: bool = False) -> bytes:
    valid = lula + flavio
    sections_total = 1000
    counted = round(sections_total * pct_counted / 100)

    def cand(number, name, votes):
        return {
            "n": str(number),
            "nmu": name,
            "nm": name,
            "vap": str(votes),
            "pvap": _br(100 * votes / valid),
            "pvapn": _br(100 * votes / valid, 9),
            "e": "s" if final and votes == max(lula, flavio) else "n",
        }

    return json.dumps(
        {
            "ele": "6258",
            "t": "2",
            "cdabr": scope,
            "dg": "25/10/2026",
            "hg": time,
            "tf": "s" if final else "n",
            "carg": [
                {
                    "cd": "1",
                    "agr": [
                        {"par": [{"sg": "PT", "cand": [cand(13, "LULA", lula)]}]},
                        {"par": [{"sg": "PL", "cand": [cand(22, "FLAVIO BOLSONARO", flavio)]}]},
                    ],
                }
            ],
            "s": {"ts": str(sections_total), "st": str(counted), "pst": _br(pct_counted), "pstn": _br(pct_counted, 9)},
            "e": {"te": "2000", "c": str(valid + 100), "a": str(2000 - valid - 100)},
            "v": {"vv": str(valid), "vb": "40", "tvn": "60"},
        }
    ).encode()
