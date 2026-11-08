"""Rapport d'activité au format Excel (openpyxl)."""
from io import BytesIO

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill
from openpyxl.utils import get_column_letter

from app.rapports.donnees import TABLES, lignes_synthese

FORMATS = {"entier": "#,##0", "fcfa": '#,##0" FCFA"', "pourcent": "0.0%", "decimal": "0.0"}
FOND_ENTETE = PatternFill("solid", fgColor="1F4E78")
FOND_SECTION = PatternFill("solid", fgColor="D9E2F3")


def _ajuster_colonnes(feuille):
    for colonne in feuille.columns:
        largeur = max(len(str(c.value)) if c.value is not None else 0 for c in colonne)
        feuille.column_dimensions[get_column_letter(colonne[0].column)].width = min(largeur + 2, 60)


def _feuille_tableau(classeur, nom, colonnes, lignes):
    feuille = classeur.create_sheet(nom)
    for j, (titre, _, _) in enumerate(colonnes, start=1):
        cellule = feuille.cell(row=1, column=j, value=titre)
        cellule.font = Font(bold=True, color="FFFFFF")
        cellule.fill = FOND_ENTETE
    for i, ligne in enumerate(lignes, start=2):
        for j, (_, cle, fmt) in enumerate(colonnes, start=1):
            valeur = ligne[cle]
            if fmt is None and isinstance(valeur, str):
                valeur = valeur.replace("_", " ")
            cellule = feuille.cell(row=i, column=j, value=valeur)
            if fmt and valeur is not None:
                cellule.number_format = FORMATS[fmt]
    feuille.freeze_panes = "A2"
    _ajuster_colonnes(feuille)


def generer_excel(rapport: dict) -> bytes:
    classeur = Workbook()
    feuille = classeur.active
    feuille.title = "Synthèse"
    feuille["A1"] = (f"Rapport d'activité — {rapport['periode']} "
                     f"du {rapport['debut']} au {rapport['fin']}")
    feuille["A1"].font = Font(bold=True, size=14)
    feuille["A2"] = (f"Généré le {rapport['genere_le']:%Y-%m-%d %H:%M}. Données de "
                     f"l'entrepôt jusqu'au {rapport['donnees_jusqu_au'] or 'n/d'}.")

    ligne = 4
    for libelle, valeur, fmt in lignes_synthese(rapport):
        cellule = feuille.cell(row=ligne, column=1, value=libelle)
        if fmt is None:
            cellule.font = Font(bold=True)
            cellule.fill = FOND_SECTION
            feuille.cell(row=ligne, column=2).fill = FOND_SECTION
        else:
            valeur_cellule = feuille.cell(row=ligne, column=2,
                                          value=valeur if valeur is not None else "n/d")
            if valeur is not None:
                valeur_cellule.number_format = FORMATS[fmt]
        ligne += 1
    _ajuster_colonnes(feuille)

    for cle, (nom_feuille, _, colonnes) in TABLES.items():
        _feuille_tableau(classeur, nom_feuille, colonnes, rapport[cle])

    sortie = BytesIO()
    classeur.save(sortie)
    return sortie.getvalue()