"""Rapport d'activité au format PDF (reportlab)."""
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.rapports.donnees import TABLES, formater, lignes_synthese

BLEU = colors.HexColor("#1F4E78")
BLEU_CLAIR = colors.HexColor("#D9E2F3")
LARGEUR_UTILE = 17 * cm
LIMITE_LIGNES = {"retards": 15}     # le PDF est une synthèse ; l'Excel contient tout


def _style_base(taille):
    return [
        ("BACKGROUND", (0, 0), (-1, 0), BLEU),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), taille),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]


def generer_pdf(rapport: dict) -> bytes:
    sortie = BytesIO()
    document = SimpleDocTemplate(
        sortie, pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm,
        topMargin=2 * cm, bottomMargin=2 * cm, title="Rapport d'activité")
    styles = getSampleStyleSheet()
    elements = [
        Paragraph("Rapport d'activité", styles["Title"]),
        Paragraph(f"Période : {rapport['periode']} du {rapport['debut']} au {rapport['fin']}",
                  styles["Normal"]),
        Paragraph(f"Généré le {rapport['genere_le']:%Y-%m-%d %H:%M}. Données de l'entrepôt "
                  f"jusqu'au {rapport['donnees_jusqu_au'] or 'n/d'}.", styles["Normal"]),
        Spacer(1, 0.5 * cm),
    ]

    # Synthèse : deux colonnes, les titres de section occupent toute la ligne
    lignes = [["Indicateur", "Valeur"]]
    sections = []
    for libelle, valeur, fmt in lignes_synthese(rapport):
        if fmt is None:
            sections.append(len(lignes))
            lignes.append([libelle, ""])
        else:
            lignes.append([libelle, formater(valeur, fmt)])
    style = _style_base(9) + [("ALIGN", (1, 0), (1, -1), "RIGHT")]
    for i in sections:
        style += [("SPAN", (0, i), (1, i)), ("BACKGROUND", (0, i), (-1, i), BLEU_CLAIR),
                  ("FONTNAME", (0, i), (-1, i), "Helvetica-Bold")]
    synthese = Table(lignes, colWidths=[11.5 * cm, 5.5 * cm], repeatRows=1)
    synthese.setStyle(TableStyle(style))
    elements.append(synthese)

    # Tableaux détaillés
    for cle, (_, titre, colonnes) in TABLES.items():
        elements += [Spacer(1, 0.6 * cm), Paragraph(titre, styles["Heading3"])]
        donnees = rapport[cle][:LIMITE_LIGNES.get(cle)]
        if not donnees:
            elements.append(Paragraph("Aucune donnée pour cette période.", styles["Normal"]))
            continue
        lignes = [[titre_col for titre_col, _, _ in colonnes]]
        for ligne in donnees:
            lignes.append([formater(ligne[c], fmt) for _, c, fmt in colonnes])
        largeur = LARGEUR_UTILE / len(colonnes)
        tableau = Table(lignes, colWidths=[largeur] * len(colonnes), repeatRows=1)
        tableau.setStyle(TableStyle(_style_base(8)))
        elements.append(tableau)
        if cle in LIMITE_LIGNES and len(rapport[cle]) > LIMITE_LIGNES[cle]:
            elements.append(Paragraph(
                f"{LIMITE_LIGNES[cle]} premières lignes sur {len(rapport[cle])} ; "
                f"liste complète dans le fichier Excel.", styles["Italic"]))

    document.build(elements)
    return sortie.getvalue()