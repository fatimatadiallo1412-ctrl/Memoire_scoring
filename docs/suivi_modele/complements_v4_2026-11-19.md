# Compléments au mémoire : modèle v4, figures, captures et sources (19/11/2026)

Tous les chiffres portent sur le modèle **en service** `xgb_home_credit_v4` (14 variables, profondeur 3, 551 arbres), avec la séparation 60 / 20 / 20 de `src/modeling.py` (validation et test : 55 647 dossiers chacun, 8,35 % de défauts).

---

## 1. Calibration par décile (v4)

Figure : `docs/figures/calibration_deciles_v4.png`

| Décile | Test : prévu | Test : observé | Écart (pt) | Validation : prévu | Validation : observé | Écart (pt) |
|---|---|---|---|---|---|---|
| 1 | 2,91 % | 2,91 % | 0,00 | 2,89 % | 3,40 % | +0,50 |
| 2 | 4,73 % | 4,78 % | +0,05 | 4,71 % | 4,91 % | +0,19 |
| 3 | 5,46 % | 5,43 % | −0,03 | 5,45 % | 5,50 % | +0,05 |
| 4 | 6,08 % | 6,50 % | +0,42 | 6,06 % | 5,80 % | −0,26 |
| 5 | 6,90 % | 6,99 % | +0,10 | 6,87 % | 6,74 % | −0,13 |
| 6 | 7,95 % | 8,21 % | +0,27 | 7,95 % | 7,57 % | −0,38 |
| 7 | 9,15 % | 8,68 % | −0,47 | 9,19 % | 9,00 % | −0,19 |
| 8 | 10,60 % | 10,30 % | −0,30 | 10,67 % | 10,50 % | −0,17 |
| 9 | 12,60 % | 12,20 % | −0,40 | 12,74 % | 12,99 % | +0,25 |
| 10 | 16,93 % | 17,45 % | **+0,52** | 17,21 % | 17,05 % | −0,16 |

- **Écart maximal : 0,52 point sur le test (décile 10), 0,50 point sur la validation (décile 1).**
- À corriger dans le texte : « inférieur à 0,5 point dans chaque décile » → « au plus 0,5 point environ ».
- Le tableau 2,54 % … 19,74 % (notebook 03, cellule 10) est celui du **modèle v1** : il ne doit plus apparaître pour v4.

## 2. Plage des scores et part au-dessus des seuils

Figure : `docs/figures/distribution_scores_v3_v4.png` (jeu de test)

| Modèle | Jeu | Score min. | Score max. | > 12 % | > 15 % | AUC |
|---|---|---|---|---|---|---|
| v3 | test | 0,24 % | 55,53 % | 20,3 % | 12,5 % | 0,6934 |
| **v4** | **test** | **0,43 %** | **37,48 %** | **17,4 %** | **7,3 %** | **0,6423** |
| v3 | validation | 0,21 % | 57,94 % | 20,7 % | 13,0 % | 0,6887 |
| **v4** | **validation** | **0,44 %** | **33,73 %** | **18,0 %** | **7,9 %** | **0,6424** |

- La plage « 0,3 % à 42,5 % » vient du modèle v1 : à remplacer.
- Lecture : v4 resserre les scores (pas de score au-delà de 37,5 %). Au seuil de 12 %, environ 17 à 18 % des dossiers sont au-dessus, contre 7 à 8 % au seuil de 15 %.

## 3. Importances SHAP (v4)

Figure : `docs/figures/importance_shap_v4.png` (validation)

Moyenne de |valeur de Shapley| en log-odds, 5 000 dossiers tirés au hasard (graine 42), TreeSHAP natif de XGBoost, colonnes one-hot regroupées par variable d'origine.

| Rang | Variable | Test | Validation |
|---|---|---|---|
| 1 | Profession | 0,251 | 0,252 |
| 2 | Âge | 0,206 | 0,207 |
| 3 | Ancienneté dans l'activité | 0,168 | 0,171 |
| 4 | Type de revenu (test) / Durée implicite (validation) | 0,141 | 0,142 |
| 5 | Durée implicite (test) / Type de revenu (validation) | 0,141 | 0,141 |
| 6 | Possède un véhicule | 0,108 | 0,107 |

- Les six premières sont les mêmes sur les deux jeux ; seuls les rangs 4 et 5 s'échangent, avec un écart de 0,001.
- Le notebook 03 (cellule 41) les calcule **sur le test** ; le chiffre sur la validation est celui à citer pour ne pas rouvrir le test.
- Le ratio montant / revenu ne pèse presque rien (0,004) : l'endettement passe par la mensualité / revenu (0,049).

### Exemple de la commerçante (profil de référence des tests)

Commerçante indépendante, 41 ans, mariée, 3 enfants, ménage de 6, locataire, ni bien immobilier ni véhicule, 5 ans d'activité, 150 000 FCFA par mois ; demande de 500 000 FCFA sur 12 mois à 24 %.

| | v3 | **v4 (en service)** |
|---|---|---|
| Probabilité de défaut | 11,56 % | **8,37 %** |
| Durée du crédit (12 mois) | −0,638 | **−0,581** |
| Taille du ménage (6) | +0,555 | **+0,325** |
| Logement (locataire) | +0,339 | **+0,261** |
| Mensualité / revenu (32 %) | +0,122 | **+0,125** |
| Type de revenu (indépendant) | −0,102 | **−0,086** |
| Véhicule (non) | +0,090 | **+0,073** |

Contributions en log-odds : positive = augmente le risque. Si le mémoire affiche −0,64 et +0,55, ce sont les valeurs v3.

---

## 4. Captures d'écran

54 captures dans `docs/captures/` (800 px de large), refaites le 19/11/2026 sur la base repeuplée en v4 au seuil de 12 %.

Nouvelles captures :
- `12_directeur_dossier_refuse_1` à `3` : dossier refusé, retour au client et recommandations ;
- `43_admin_sante_modele_1` à `3` : page Santé du modèle ;
- `53_client_refus_recommandations_1` et `2` : refus vu par le client.

---

## 5. Sources demandées

Les références ci-dessous sont des ouvrages de référence. **Vérifiez l'édition et les pages sur l'exemplaire que vous citez** : aucun numéro de page n'est donné ici.

### Entrepôt de données (section 2.2 : schéma en étoile, faits et dimensions, Kimball et Inmon)

- Kimball, R., & Ross, M. (2013). *The Data Warehouse Toolkit: The Definitive Guide to Dimensional Modeling* (3ᵉ éd.). Wiley.
  Soutient : la modélisation dimensionnelle, le schéma en étoile, la distinction faits / dimensions, le grain d'une table de faits, les dimensions conformes, l'approche « bottom-up » par magasins de données. C'est la référence du schéma en étoile de `etl/chargement_dwh.sql`.
- Inmon, W. H. (2005). *Building the Data Warehouse* (4ᵉ éd.). Wiley.
  Soutient : la définition classique de l'entrepôt (orienté sujet, intégré, non volatil, historisé) et l'approche « top-down ». Nécessaire puisque le plan annonce « Kimball et Inmon ».

### UML (diagrammes de cas d'utilisation, d'activité, de séquence)

- Object Management Group (2017). *OMG Unified Modeling Language (OMG UML), Version 2.5.1* (document formal/17-12-05). Spécification officielle, disponible sur le site de l'OMG.
  Soutient : la définition normative de chaque diagramme et de sa notation.
- Booch, G., Rumbaugh, J., & Jacobson, I. (2005). *The Unified Modeling Language User Guide* (2ᵉ éd.). Addison-Wesley.
  Soutient : l'usage pédagogique des diagrammes, par les trois auteurs du langage. Plus facile à citer que la spécification pour expliquer un diagramme.

### Crédit progressif (recommandation « commencer par un petit montant, puis augmenter »)

- Armendáriz, B., & Morduch, J. (2010). *The Economics of Microfinance* (2ᵉ éd.). MIT Press.
  Soutient : les « incitations dynamiques » et le prêt progressif (« progressive lending ») comme mécanisme de la microfinance : l'accès à un crédit plus important dépend du bon remboursement du précédent.
- Morduch, J. (1999). The Microfinance Promise. *Journal of Economic Literature*, 37(4), 1569-1614.
  Soutient : la même idée dans un article de synthèse très cité, avec la discussion de ses limites.

Ce que ces sources ne permettent pas : elles ne mesurent pas l'effet du crédit progressif au Sénégal ni dans votre institution. Le conseil de l'application (`src/recours.py`) reste une recommandation de politique, à présenter comme telle.
