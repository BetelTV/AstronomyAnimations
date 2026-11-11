#!/usr/bin/env python3
"""
gerar_site.py — monta a pasta docs/ (site do GitHub Pages) a partir de src/.

    python gerar_site.py            # gera docs/
    python gerar_site.py --servir   # gera e abre um servidor local em http://localhost:8000

Os parâmetros abaixo vêm dos modelos originais do GeoGebra (TCC, 2021) e são injetados nas páginas.
O movimento é calculado no navegador (JavaScript/Three.js) para que a animação seja contínua;
o mesmo cálculo existe em Python no arquivo efemerides.py, para conferir números e gerar tabelas.
"""
import json
import shutil
import sys
from pathlib import Path

CONFIG = {
    "ano": 2026,
    # Modelo 2: local inicial (o arquivo do GeoGebra usa latitude ≈ −11,31°)
    "local_inicial": "São Paulo",
    "locais": [
        {"nome": "São Paulo (SP)", "lat": -23.55, "lon": -46.63, "fuso": -3},
        {"nome": "Campinas (SP)", "lat": -22.91, "lon": -47.06, "fuso": -3},
        {"nome": "Cuiabá (MT)", "lat": -15.60, "lon": -56.10, "fuso": -4},
        {"nome": "Latitude do TCC (−11,31°)", "lat": -11.31, "lon": -56.10, "fuso": -4},
        {"nome": "Macapá (Linha do Equador)", "lat": 0.03, "lon": -51.07, "fuso": -3},
        {"nome": "Ubatuba (Trópico de Capricórnio)", "lat": -23.44, "lon": -45.07, "fuso": -3},
        {"nome": "Porto Alegre (RS)", "lat": -30.03, "lon": -51.23, "fuso": -3},
        {"nome": "Lisboa (Portugal)", "lat": 38.72, "lon": -9.14, "fuso": 0},
        {"nome": "Tromsø (Círculo Polar Ártico)", "lat": 69.65, "lon": 18.96, "fuso": 1},
        {"nome": "Polo Sul", "lat": -90.0, "lon": 0.0, "fuso": 0},
    ],
}

RAIZ = Path(__file__).resolve().parent
SRC, DOCS = RAIZ / "src", RAIZ / "docs"


def main():
    DOCS.mkdir(exist_ok=True)
    cfg = json.dumps(CONFIG, ensure_ascii=False)
    for arq in SRC.iterdir():
        if arq.is_dir():
            shutil.copytree(arq, DOCS / arq.name, dirs_exist_ok=True)
        elif arq.suffix == ".html":
            (DOCS / arq.name).write_text(arq.read_text(encoding="utf-8").replace("/*CONFIG*/{}", cfg),
                                         encoding="utf-8")
        else:
            shutil.copy2(arq, DOCS / arq.name)
    (DOCS / ".nojekyll").write_text("")
    print("Site gerado em", DOCS)
    if "--servir" in sys.argv:
        import functools, http.server, webbrowser
        h = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(DOCS))
        print("Abrindo http://localhost:8000  (Ctrl+C para parar)")
        webbrowser.open("http://localhost:8000")
        http.server.ThreadingHTTPServer(("localhost", 8000), h).serve_forever()


if __name__ == "__main__":
    main()
