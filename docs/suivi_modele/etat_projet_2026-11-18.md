# État du projet au 18/11/2026 : modèle, seuil, tests, équité

Chaque ligne donne la valeur exacte et sa source (fichier ou commande). Fichiers de sortie produits aujourd'hui :
`docs/suivi_modele/audit_complements_validation.json` (validation, `python -m src.audit_complements`),
`docs/suivi_modele/evaluation_test_v4.json` (test, `python -m src.evaluation_test`),
`docs/suivi_modele/simulation_rescoree_v4.json` (simulation rescorée, sans écriture en base),
`docs/suivi_modele/audit_equite_validation.txt` (`python -m src.audit_equite`).

---

## 1. Modèle en service et seuil

| Question | Réponse | Source |
|---|---|---|
| Modèle en service | `xgb_home_credit_v4.joblib` (XGBoost, 14 variables, 551 arbres, profondeur 3, taux 0,03, monotonie croissante sur `credit_sur_revenu`, `annuite_sur_revenu`, `duree_implicite`) | `app/scoring.py:20` (`MODELE_VERSION`, défaut v4, pas de surcharge dans `.env`), `src/modeling.py` |
| Seuil appliqué | **12 %** (probabilité de défaut ≤ 0,12 → dans la politique) ; 9,6 % si incident passé régularisé (× 0,8) | `app/parametres.py:8` ; base : `ops.parametre.seuil_defaut = 0.1200` |
| Changement | 15 % → 12 % le **11/11/2026** | commit `d5575a7` ; `docs/audit_application_2026-11-11.md`, § « Révision du seuil de risque » |
| Motif | choix en faveur de l'inclusion : 82,6 % de dossiers acceptés, défaut chez les acceptés 6,88 % (< moyenne 8,35 %) et égal à la prévision ; au-delà de 12 %, la tranche ajoutée fait défaut à ~13 % | idem |
| Attention | la grille ayant fixé 12 % a été calculée **sur le test**. Refaite aujourd'hui sur la **validation**, elle donne des chiffres quasi identiques (écarts ≤ 0,6 point, voir tableau ci-dessous) : le choix peut s'appuyer sur la validation | commande ci-dessous |

Grille des seuils, v4, **validation** (55 647 dossiers) :

| Seuil | Acceptés | Défaut chez les acceptés | Prévu chez les acceptés | Défaut chez les refusés |
|---|---|---|---|---|
| 6 % | 34,0 % | 4,77 % | 4,53 % | 10,19 % |
| 8 % | 55,6 % | 5,49 % | 5,45 % | 11,92 % |
| 10 % | 70,9 % | 6,20 % | 6,21 % | 13,58 % |
| **12 %** | **82,0 %** | **6,83 %** | **6,85 %** | **15,26 %** |
| 15 % | 92,2 % | 7,54 % | 7,56 % | 17,75 % |

---

## 2. Résultats du modèle en service

### Home Credit, v4 (en service)

| Mesure | Test | Validation | Source |
|---|---|---|---|
| AUC | **0,6423** (IC95 DeLong [0,6341 ; 0,6505], bootstrap [0,6342 ; 0,6511]) | 0,6424 | `evaluation_test_v4.json` ; `audit_complements_validation.json` |
| Gini (2 × AUC − 1) | 0,2846 | 0,2848 | idem |
| KS | 0,2032 | 0,2132 | idem |
| Brier | 0,07487 (référence taux constant : 0,07649) | 0,07485 | idem |
| PR-AUC | 0,1389 (hasard : 0,0835) | 0,1398 | idem |

Rappel v3 (test, n'est plus en service) : AUC 0,6934, KS 0,2835, PR-AUC 0,1741, Brier 0,0733 (`notebooks/03_modelisation.ipynb`, cellule 39). La perte de ~0,05 d'AUC vient de la contrainte sur la durée (motif en dents de scie de Home Credit, non transposable).

### Credit Risk Dataset (validation externe de la démarche, modèle propre à ce jeu, **non ré-entraîné** pour v4)

| Mesure | Valeur | Source |
|---|---|---|
| AUC validation : régression logistique / forêt / XGBoost libre / XGBoost monotone réglé | 0,7946 / 0,8187 / 0,8230 / 0,8263 | `notebooks/04_validation_credit_risk.ipynb`, cellules 3-6 |
| Test (XGBoost monotone, 255 arbres, profondeur 4) | AUC 0,8361 ; Gini 0,6722 ; KS 0,5162 ; Brier 0,1044 ; PR-AUC 0,7219 (défaut 21,9 %) | cellule 8 |

### Tableau comparatif, mêmes 14 variables que v4, **validation**

| Modèle | AUC | KS | Brier | PR-AUC |
|---|---|---|---|---|
| Régression logistique (C = 1) | 0,6324 | 0,2033 | 0,07507 | 0,1358 |
| Régression logistique réglée (grille C 10⁻⁴ à 100 × pondération des classes ; meilleur C = 100, `balanced`) | 0,6325 | | | |
| Régression logistique réglée + âge et ancienneté en classes | 0,6330 | 0,2023 | 0,07503 | 0,1376 |
| XGBoost non réglé (300 arbres, profondeur 3, mêmes contraintes) | 0,6417 | 0,2130 | 0,07487 | 0,1396 |
| **XGBoost réglé (v4 en service)** | **0,6424** | **0,2132** | **0,07485** | **0,1398** |

Source : `audit_complements_validation.json`, clé `comparaison_validation`.

- **La régression logistique a-t-elle été réglée avec le même soin ?** Dans le notebook 03, non (C = 1 par défaut, et sur l'ancien jeu de variables : 0,6401 en validation). C'est fait aujourd'hui : la grille complète sur C et la pondération ne gagne que 0,0001, et le découpage de l'âge et de l'ancienneté en classes 0,0006. L'écart avec XGBoost (≈ 0,01) ne vient donc pas d'un réglage inégal.
- Le tableau de 2.4.3 (0,6401 / 0,6652 / 0,6842 / 0,6949) porte sur l'**ancien jeu de variables** (v1, avec montants bruts et éducation). Pour v4, utiliser le tableau ci-dessus.
- Le réglage de XGBoost apporte peu (+0,0007) ; la validation croisée à 5 blocs le confirme : 0,6441 ± 0,0028 (`docs/suivi_modele/experience_hyperparametres.md`).

---

## 3. Ouvertures du jeu de test

### Home Credit : 10 ouvertures (le texte « une seule fois » ou « trois fois » est inexact)

| N° | Date (commit) | Objet | Choix de conception tiré du test ? | Source |
|---|---|---|---|---|
| 1 | 05/11 | évaluation finale v1 (régression, forêt, XGBoost v1) | non | notebook 03, cellule 15 |
| 2 | 05/11 | évaluation v2 (sans montants bruts) | non (choix v2 fait sur la validation) | cellule 19 |
| 3 | 05/11 | suggestion de montant sur 300 dossiers du test (v2) | **oui : `ratio_min` = 50 %** | cellules 24-28 |
| 4 | 05/11 | audit d'équité v2 (sexe, éducation) | **oui : retrait de l'éducation** | cellule 29 |
| 5 | 05/11 | évaluation v3, comparaison v2/v3 par groupe, suggestion v3 | non | cellules 31, 33 |
| 6 | 11/11 | évaluation v4 (comparaison v3/v4, calibration, équité à 15 %, SHAP sur un échantillon du test) ; `src/modeling.py` affiche aussi l'AUC test à l'entraînement | non (variante B choisie sur la validation) | cellules 39-41 |
| 7 | 11/11 | grille des seuils 6 à 15 % | **oui : seuil 12 %** | `docs/audit_application_2026-11-11.md` |
| 8 | 17/11 | AUC test des 4 variantes de la validation croisée | non (« modèle conservé tel quel ») | `src/experiences.py` |
| 9 | 17-18/11 | recalcul de la parité par sexe à 12 % | non | session de travail (pas de script) |
| 10 | 18/11 | évaluation finale (IC de l'AUC, matrice de confusion, pente de calibration) | non | `src/evaluation_test.py` |

À écrire dans le mémoire : trois choix ont été faits sur le test (ratio minimal, retrait de l'éducation, seuil 12 %). Deux sont aujourd'hui revérifiés sur la validation avec le même résultat (éducation : § 4.5 ; seuil : § 1). Le `ratio_min` ne l'est pas encore. Les audits d'équité de 4.1.10 (`src/audit_equite.py`, `src/audit_complements.py`) n'ouvrent pas le test.

### Credit Risk Dataset : **1 ouverture** (notebook 04, cellule 8). Tous les réglages sont faits sur la validation.

### Retrait de l'éducation : décidé **sur le test** (ouverture 4, notebook 03, cellule 29, modèle v2). Écrire que la décision a été prise sur le test, puis confirmée sur la validation le 18/11 (§ 4.5).

---

## 4. Audit d'équité du modèle en service (v4, **validation**, n = 55 647 ; 55 647 avec sexe F/M)

Définitions : acceptation = p ≤ seuil ; égalité des chances (TPR) = part acceptée parmi les bons payeurs (TARGET = 0) ; FPR = part acceptée parmi les défaillants (TARGET = 1) ; rapport = groupe / groupe le plus favorisé (le moins favorisé au numérateur). IC95 de Wilson sur les taux, bootstrap (1 000 tirages) sur les écarts.

### 4.1 Par sexe

| | Femmes | Hommes | Rapport H/F |
|---|---|---|---|
| Dossiers | 36 534 | 19 113 | |
| Défaut observé | 7,17 % | 10,60 % | |
| Défaut prévu (calibration) | 7,85 % | 9,37 % | |
| AUC | 0,6339 | 0,6359 | écart F − H = −0,0020, IC95 [−0,0185 ; +0,0156] |
| **Seuil 12 %** : acceptation | 85,71 % | 75,00 % | **0,875** |
| égalité des chances (TPR) | 86,69 % | 76,84 % | **0,886** [0,878 ; 0,895] |
| défaillants acceptés (FPR) | 73,07 % [71,34 ; 74,74] | 59,48 % [57,32 ; 61,59] | 0,814 |
| défaut chez les acceptés | 6,11 % | 8,41 % | |
| **Seuil 15 %** : acceptation | 94,48 % | 87,71 % | 0,928 |
| égalité des chances (TPR) | 94,96 % | 88,98 % | 0,937 [0,931 ; 0,943] |
| défaillants acceptés (FPR) | 88,20 % | 77,00 % | 0,873 |
| défaut chez les acceptés | 6,69 % | 9,31 % | |

Proxy : un modèle retrouve le sexe à partir des 14 variables avec une AUC de 0,8625 [0,8594 ; 0,8657] ; sans la profession 0,774 ; sans profession ni véhicule 0,717 (`audit_equite_validation.txt`).

### 4.2 Par âge (cinq tranches ; le texte en annonce quatre, à corriger)

| Tranche | n | Défaut observé | Défaut prévu | AUC | Accept. 12 % (rapport) | TPR 12 % (rapport) | FPR 12 % | Accept. 15 % (rapport) | TPR 15 % (rapport) | FPR 15 % |
|---|---|---|---|---|---|---|---|---|---|---|
| < 30 ans | 7 812 | 11,66 % | 12,16 % | 0,599 | 52,75 % (0,528) | 54,40 % (0,545) | 40,29 % | 75,96 % (0,760) | 77,31 % (0,773) | 65,75 % |
| 30-39 ans | 14 903 | 10,00 % | 10,08 % | 0,644 | 70,74 % (0,709) | 72,52 % (0,726) | 54,73 % | 87,07 % (0,871) | 88,29 % (0,883) | 76,12 % |
| 40-49 ans | 13 716 | 7,94 % | 7,99 % | 0,631 | 88,48 % (0,886) | 89,46 % (0,896) | 77,13 % | 96,54 % (0,966) | 96,99 % (0,970) | 91,37 % |
| 50-59 ans | 12 411 | 6,53 % | 6,23 % | 0,593 | 97,15 % (0,973) | 97,44 % (0,976) | 92,96 % | 99,32 % (0,994) | 99,39 % (0,994) | 98,40 % |
| 60 ans et + | 6 805 | 5,04 % | 4,99 % | 0,565 | 99,82 % (réf.) | 99,83 % (réf.) | 99,71 % | 99,96 % (réf.) | 99,95 % (réf.) | 100 % |

Lecture : la calibration est bonne dans chaque tranche (écart ≤ 0,5 point) ; l'écart d'acceptation suit un écart réel de défaut (11,7 % contre 5,0 %). Les moins de 30 ans restent sous 0,8 aux deux seuils.

### 4.3 Modèles sans âge et sans profession (mêmes réglages que v4, validation)

| Variante | AUC | Rapport H/F accept. 12 % | TPR H/F 12 % | TPR < 30 ans 12 % | TPR < 30 ans 15 % |
|---|---|---|---|---|---|
| v4 (en service) | 0,6424 | 0,875 | 0,886 | 0,545 | 0,773 |
| sans âge | 0,6337 (−0,009) | 0,877 | 0,889 | **0,695** | 0,872 |
| sans profession | 0,6306 (−0,012) | **0,981** | **0,988** | 0,533 | 0,774 |

Lecture : retirer l'âge réduit l'écart entre jeunes et aînés sans le faire disparaître (l'ancienneté et la situation familiale relaient l'âge) ; retirer la profession fait presque disparaître l'écart entre sexes, ce qui confirme qu'elle est le principal relais du sexe. Chacun coûte environ 0,01 d'AUC. Aucune des deux variantes n'est mise en service (décision à justifier dans le mémoire).

### 4.4 IC de l'écart d'AUC entre sexes : F − H = −0,0020, IC95 bootstrap [−0,0185 ; +0,0156] (v4) : pas de différence de qualité de classement.

### 4.5 Retrait de l'éducation (v2 → v3), recalculé sur la **validation**

| | v2 (avec éducation) | v3 (sans éducation) |
|---|---|---|
| AUC validation | 0,6917 | 0,6887 |
| Rapport H/F d'acceptation, 15 % / 12 % | 0,914 / 0,873 | 0,920 / 0,878 |
| Acceptation 15 %, études supérieures | 97,16 % | 91,85 % |
| Acceptation 15 %, secondaire / secondaire inférieur | 83,62 % / 78,13 % | 85,74 % / 82,87 % |
| Rapport le plus bas entre niveaux d'éducation, 15 % | 0,804 (secondaire inférieur) | 0,894 (supérieur incomplet) |

Sur le test (décision d'origine, notebook 03, cellule 31, seuil 15 %) : rapport H/F 0,915 → 0,919. Le retrait vise l'équité entre niveaux d'éducation, pas entre sexes ; il coûte 0,003 d'AUC.

---

## 5. Éléments de 2.4 « à calculer » (test, ouverture n° 10)

| Mesure | Seuil 12 % (en service) | Seuil 15 % |
|---|---|---|
| Défaillants refusés (VP) | 1 480 | 745 |
| Bons payeurs refusés (FP) | 8 202 | 3 336 |
| Défaillants acceptés (FN) | 3 164 | 3 899 |
| Bons payeurs acceptés (VN) | 42 801 | 47 667 |
| Rappel (défauts détectés) | 31,9 % | 16,0 % |
| Précision (refus justifiés) | 15,3 % | 18,3 % |
| Spécificité (bons payeurs acceptés) | 83,9 % | 93,5 % |
| Taux d'acceptation | 82,6 % | 92,7 % |
| Défaut chez les acceptés | 6,88 % | 7,56 % |

Calibration (Van Calster) : pente 0,981 [0,922 ; 1,041] ; intercept (calibration dans l'ensemble) 0,002 [−0,029 ; 0,032] ; prévu moyen 8,33 % contre 8,35 % observé. IC de l'AUC : voir § 2. Source : `evaluation_test_v4.json`.

PSI entre la validation Home Credit et les 1 507 demandes simulées (v4) : **score 0,075** (stable, < 0,10), mais variables très décalées : `duree_implicite` 4,88, profession 3,24, logement 2,56, taille du ménage 1,78, type de revenu 1,27 (> 0,25 = dérive forte). Lecture : la population simulée est structurellement différente de Home Credit, comme attendu, mais la distribution des scores reste proche. Source : `simulation_rescoree_v4.json`.

---

## 6. Simulation sénégalaise

| Question | Réponse | Source |
|---|---|---|
| 1 044 / 261 / 195 encore vrais ? | **Non.** Ces chiffres viennent du modèle **v3 au seuil de 15 %** ; la base contient 1 045 / 263 / 199 pour 1 507 demandes scorées | `ml.score` (version `xgb_home_credit_v3`, seuil 0,15) |
| Avec v4 et le seuil de 12 % (rescorées, sans écriture en base) | **1 098 accords (72,9 %), 176 accords réduits (11,7 %), 233 refus (15,5 %)** sur 1 507 | `simulation_rescoree_v4.json` |
| Passages v3 → v4 | 946 accords restent accords ; 120 accords réduits deviennent accords ; 49 accords deviennent refus ; 32 refus deviennent accords | idem |
| Score moyen des simulés (v4) | 9,77 % (médiane 8,44 %, de 1,5 % à 42,3 %) contre 8,38 % en validation Home Credit | idem |
| Audit d'inclusion (2 000 profils, v4, 12 %) | 1 617 accords, 253 accords réduits, 130 refus | `data/processed/audit_inclusion_profils.csv` (`simulation/audit_inclusion.py`) |

Pour que la base (et donc l'application et Metabase) reflète v4 à 12 %, il faut relancer `simulation/peupler.py` ; ce n'est pas fait.
