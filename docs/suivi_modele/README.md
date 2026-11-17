# Cycle de vie du modèle en production

Le modèle v4 a appris sur Home Credit. Dans une institution réelle, il sert de **point de départ**. On l'adapte ensuite aux données de l'institution, sous surveillance continue.

| Étape | Quand | Commande | Ce qu'elle produit |
|---|---|---|---|
| Figer la référence | une fois, après 6 à 12 mois de production | `python -m src.surveillance figer-reference --debut … --fin …` | `models/reference_<version>.json` |
| Rapport de suivi | le 1er de chaque mois (automatique, `app/planificateur.py`) | `python -m src.surveillance rapport --debut … --fin …` | `suivi_<date>.md` / `.json` |
| Champion / challenger | alerte rouge, ou une fois par an | `python -m src.champion_challenger` | `champion_challenger_<date>.md` |
| Mise en service | après validation par la direction | `MODELE_VERSION=<version>` dans `.env`, puis redémarrage de l'API | chaque score garde sa version (`ml.score.version_modele`) |

## Indicateurs du rapport mensuel

- **Stabilité (sans attendre les remboursements).** PSI des scores et de chaque variable, comparé à la population de référence. Seul l'excès au-delà du bruit d'échantillonnage déclenche une alerte : sur 130 dossiers, le hasard seul donne déjà un PSI d'environ 0,08.
- **Modalités inconnues.** Une profession absente des données d'entraînement est ignorée sans erreur par le modèle. Le rapport compte ces dossiers et en donne des exemples.
- **Décisions.** Taux d'acceptation et taux de dérogation (décisions contraires à la recommandation), avec le sens de chaque dérogation.
- **Performance.** Sur les crédits *mûrs* : la fenêtre d'observation (min(durée, 12 mois) + 90 jours) est terminée. On mesure l'AUC par rapport à la fiche du modèle et la calibration (défaut prévu contre défaut observé). En dessous de 30 défauts, la performance n'est pas jugée.

Les seuils (PSI 0,10 / 0,25, dérogations 15 % / 25 %, baisse d'AUC 0,03 / 0,05, calibration ×1,25 / ×1,5) sont des valeurs d'usage courant. Ils sont à valider par la direction des risques, en tête de `src/surveillance.py`.

## Adapter le modèle (`src/recalibration.py`)

1. **Recalibration.** Les arbres ne changent pas ; seul le niveau des probabilités est corrigé. La méthode dépend du nombre de défauts locaux : décalage (< 30), Platt (30 à 199), isotonique (≥ 200). Toutes ces corrections sont croissantes : le classement des clients, les contraintes de monotonie et la recherche du montant accordable restent valides.
2. **Réentraînement.** On ajoute des arbres appris sur les crédits locaux, puis on recalibre. La démarche n'est tentée qu'à partir de 200 défauts locaux.

Un challenger n'est **promouvable** que si toutes ces conditions sont remplies :

- au moins 30 défauts dans la période d'évaluation hors période ;
- un Brier meilleur que celui du champion ;
- une AUC qui ne baisse pas de plus de 0,01 ;
- un écart hommes / femmes de la part des dossiers au-dessus du seuil qui ne s'accroît pas de plus de 2 points.

Chaque version enregistrée a sa fiche (`models/<version>.json`) : données, performances, équité, validation.

## Limites connues

- **Biais de sélection.** Les remboursements ne sont observés que pour les crédits accordés. Le modèle apprend donc de moins en moins sur les profils refusés. Correctifs possibles : inférence des refusés, ou accords encadrés de petits montants juste au-dessus du seuil.
- **Données simulées.** Les remboursements de `simulation/rembourser.py` ne dépendent pas du score. Les rapports produits sur cette base valident le **fonctionnement** des outils, pas le modèle.
