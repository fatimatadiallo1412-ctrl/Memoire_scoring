"""Rend les diagrammes Mermaid (docs/uml/*.mmd) en SVG et PNG.

Usage : python docs/uml/rendre.py [nom ...]
Mermaid est lu en local (MERMAID_JS, par défaut la copie fournie avec RStudio/Quarto) :
aucun accès réseau. Nécessite Playwright et son Chromium (pip install playwright).
"""
import json
import os
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ICI = Path(__file__).resolve().parent
MERMAID = os.environ.get(
    "MERMAID_JS", "/usr/lib/rstudio/resources/app/bin/quarto/share/formats/html/mermaid/mermaid.min.js")
CONFIG = {
    "startOnLoad": False, "theme": "base", "securityLevel": "loose",
    "fontFamily": "Inter, 'DejaVu Sans', Arial, sans-serif",
    "themeVariables": {
        "fontSize": "15px", "primaryColor": "#eef3fb", "primaryBorderColor": "#2f5d8f",
        "primaryTextColor": "#14213d", "lineColor": "#44546a", "secondaryColor": "#fdf3e1",
        "tertiaryColor": "#ffffff", "noteBkgColor": "#fff8c5", "noteBorderColor": "#b08800",
        "actorBkg": "#eef3fb", "actorBorder": "#2f5d8f", "signalColor": "#44546a",
        "labelBoxBkgColor": "#eef3fb", "labelBoxBorderColor": "#2f5d8f",
    },
    "sequence": {"showSequenceNumbers": True, "wrap": True, "width": 210, "messageMargin": 34,
                 "noteMargin": 12, "actorMargin": 110, "mirrorActors": False},
    "flowchart": {"curve": "basis", "htmlLabels": True, "nodeSpacing": 26, "wrappingWidth": 330, "rankSpacing": 46},
    "er": {"layoutDirection": "TB"},
    # Halo blanc derrière les textes : ils restent lisibles quand ils croisent une ligne de vie.
    "themeCSS": ".messageText, .loopText, .loopText tspan, .labelText, .labelText tspan, text.actor { paint-order: stroke; stroke: #ffffff;"
                " stroke-width: 5px; stroke-linejoin: round; }",
}


def main(noms):
    fichiers = sorted(ICI.glob("*.mmd"))
    if noms:
        fichiers = [f for f in fichiers if f.stem in noms]
    with sync_playwright() as p:
        nav = p.chromium.launch()
        page = nav.new_page(device_scale_factor=2, viewport={"width": 1600, "height": 1200})
        page.set_content("<html><body style='margin:0;background:white'><div id='d'></div></body></html>")
        page.add_script_tag(path=MERMAID)
        page.evaluate(f"mermaid.initialize({json.dumps(CONFIG)})")
        for f in fichiers:
            code = f.read_text(encoding="utf-8")
            try:
                svg = page.evaluate("async (c) => (await mermaid.render('g' + Date.now(), c)).svg", code)
            except Exception as e:
                print("ÉCHEC", f.name, str(e).splitlines()[0][:300])
                continue
            (ICI / f"{f.stem}.svg").write_text(svg, encoding="utf-8")
            page.evaluate("(s) => { document.getElementById('d').innerHTML = s; }", svg)
            el = page.locator("#d svg")
            largeur = page.evaluate("() => document.querySelector('#d svg').viewBox.baseVal.width")
            page.evaluate(f"() => {{ const s = document.querySelector('#d svg'); s.style.maxWidth = 'none'; s.setAttribute('width', {largeur}); }}")
            el.screenshot(path=str(ICI / f"{f.stem}.png"), omit_background=False)
            print("ok", f.stem)
        nav.close()


if __name__ == "__main__":
    main(sys.argv[1:])
