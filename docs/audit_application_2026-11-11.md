# Audit de l'application Yokkuté — 11 novembre 2026

Périmètre : API FastAPI (`app/`), modèle de scoring (`src/`, `models/`, notebooks), base PostgreSQL (lecture seule), front React (`frontend/`).
Méthode : lecture du code, tests automatisés ad hoc contre l'API locale et la base (aucune écriture en base), tests du modèle chargé, lint et build du front.
Il n'existe pas de suite de tests automatisés dans le dépôt : tous les tests ci-dessous ont été lancés pendant l'audit.

---

## 1. Synthèse

| Priorité | Constat | Effort |
|---|---|---|
| 🔴 Critique | Clé de signature des jetons (`SECRET_KEY`) de **9 octets** : un attaquant peut la retrouver par force brute et fabriquer un jeton administrateur. | 5 min |
| 🔴 Critique | Les **produits affichés sur le site** (commerce, artisan, agricole, équipement, jusqu'à 25 M FCFA et 5 ans) **n'existent pas en base** : la base contient MICRO, PME, SALARIE (max 5 M FCFA, 24 mois). Une demande à 25 M FCFA ou 5 ans est refusée par l'API. | 1 h |
| 🟠 Élevé | Le modèle n'a **jamais vu de crédits de moins de 8 mensualités** (`duree_implicite` min = 8,04). Les 304 demandes de 6 mois en base et les produits de 3 mois sont hors domaine : un crédit de 6 mois sort plus risqué (26 %) qu'un crédit de 12 mois (12 %). | 0,5 à 2 j |
| 🟠 Élevé | « Score explicable » : l'application n'affiche que deux motifs globaux (`risque_modele`, `endettement`) et les paramètres. Il n'y a **pas d'explication par variable** pour chaque client (SHAP), alors que le notebook la calcule. | 0,5 j |
| 🟠 Élevé | Le directeur ne voit que les **50 derniers dossiers** (limite fixée dans le front) sur 1 506 ; la pagination ajoutée se limite donc à 5 pages. Il faut paginer côté API. | 0,5 j |
| 🟡 Moyen | Un « accord avec modification » change montant/durée **sans recalculer le risque** de ce nouveau montant. | 2 h |
| 🟡 Moyen | Le mot de passe changé ou le compte réinitialisé **n'invalide pas** les jetons déjà émis (durée de vie 8 h). | 2 h |
| 🟡 Moyen | Énumération des comptes par mesure du temps de réponse à la connexion (argon2 n'est exécuté que pour les comptes existants). | 30 min |
| 🟡 Moyen | Deux paiements simultanés peuvent dépasser le reste à payer (pas de verrou de ligne). | 1 h |
| 🟡 Moyen | Aucune suite de tests automatisés. | 1 à 2 j |
| 🟢 Faible | `index.html` déclare `lang="en"` (lecteurs d'écran, SEO). CORS n'autorise que le port 5173. Fichiers morts côté front. Bundle unique de 448 Ko. | 1 h |

**Ce qui est solide** : cloisonnement des rôles et des portefeuilles (55 routes testées), hachage argon2, verrouillage après 5 échecs, registre des paiements en ajout seul, motif obligatoire en cas de désaccord avec le modèle, score périmé si le dossier change, modèle bien validé (AUC test 0,698, calibration excellente, audit d'équité).

---

## 2. Ce que tu as demandé et ce qui est produit

| Demande | État | Vérification |
|---|---|---|
| Design system, aucun dégradé | ✅ | aucune occurrence de `gradient` dans `frontend/src` |
| Textes affichés inchangés (avant les demandes de nouveaux textes) | ✅ | comparaison automatique des textes JSX avec la version commitée |
| Hero en tableau de bord, titre et texte fournis, carte de scoring (8,2 %, risque faible, prêt accordé) | ✅ | rendu vérifié |
| Photo réaliste, pas un dessin | ⚠️ | la photo Pexels (vraie personne) est toujours en place, en attendant ta photo à déposer dans `frontend/public/images/cliente-demo.jpg` |
| Pagination des listes | ⚠️ | faite côté interface, mais limitée par l'API (voir § 1) |
| « Ouvrir » et « Retour » en boutons | ✅ | build OK ; pages internes non vues à l'écran |
| Partie admin redessinée | ✅ | build OK ; non vue à l'écran (connexion nécessaire) |
| Téléphone sénégalais à 9 chiffres (70, 71, 75, 76, 77, 78) | ✅ | formulaires + API ; 1 506 / 1 506 téléphones en base conformes |
| E-mails `@gmail.com` | ✅ (création) | 0 compte existant en `@gmail.com` : la connexion n'impose donc pas la règle, volontairement |
| Montants et durées des produits | ⚠️ | affichés sur la page, **mais absents de la base** (voir § 1) |
| Footer compact | ✅ | rendu vérifié |

---

## 3. Sécurité (API)

### Tests réalisés
- **Sans jeton** : les 55 routes protégées répondent 401. ✅
- **Jeton forgé `alg=none`** : refusé (401). ✅
- **Matrice des rôles** (administrateur, gestionnaire, client, directeur) sur toutes les routes GET : chaque rôle n'accède qu'à ses routes (403 sinon). ✅
- **Cloisonnement** : un gestionnaire reçoit 404 sur un client ou un dossier hors portefeuille ; un client reçoit 404 sur le crédit d'un autre client. ✅
- **CORS** : une origine étrangère est refusée. ✅
- **Validation** : un e-mail non Gmail est refusé (422) par `/contact`. ✅

### À corriger
1. **`SECRET_KEY` trop courte (9 octets)** — PyJWT émet `InsecureKeyLengthWarning`.
   Correction : générer une clé de 64 caractères et refuser de démarrer si elle fait moins de 32 octets :
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(48))"
   ```
   puis, dans `app/security.py`, lever une erreur si `len(CLE_SECRETE.encode()) < 32`.
2. **Révocation des jetons** : ajouter une colonne `version_jeton` à `utilisateur`, l'inclure dans le jeton et l'incrémenter au changement ou à la réinitialisation du mot de passe et à la désactivation.
3. **Temps constant à la connexion** : quand le compte n'existe pas, vérifier quand même un hachage factice.
4. **Paiements concurrents** : charger le crédit avec `with_for_update()` avant de calculer le reste à payer.
5. **Limitation de débit en mémoire** (`/contact`, `/reinitialisations`, comptes inconnus) : elle est remise à zéro au redémarrage et ne fonctionne pas avec plusieurs processus. C'est acceptable pour le mémoire ; en production, il faudrait passer par Redis ou la base.
6. **`/docs` public** : à désactiver en production (`FastAPI(docs_url=None)` selon l'environnement).

---

## 4. Modèle de scoring

### Ce qui est solide
- XGBoost avec **contraintes de monotonie** sur les deux ratios d'endettement : vérifié, la probabilité de défaut croît bien avec le montant (de 7,7 % à 12,8 % entre 100 000 et 2 000 000 FCFA, pour un revenu de 150 000).
- Variables **sans unité monétaire** : transposables au FCFA.
- Test final : AUC 0,698 ; PR-AUC 0,178 ; KS 0,296 ; Brier 0,0731. Calibration à moins de 0,6 point par décile.
- Audit d'équité (sexe, éducation), sexe exclu du modèle.
- Temps de réponse : chargement 0,05 s ; une probabilité en 30 à 100 ms ; recherche du montant suggéré en moins de 60 ms.

### Points faibles
1. **Durées courtes hors domaine** (le point le plus important pour la microfinance) : dans les données d'entraînement, `duree_implicite` (montant / mensualité) vaut au minimum 8,04. Mesure sur un même client (revenu 150 000, montant 1 000 000) :

   | Durée | 6 mois | 12 mois | 24 mois | 60 mois |
   |---|---|---|---|---|
   | Probabilité de défaut | 26,2 % | 12,3 % | 22,7 % | 16,8 % |

   Le modèle pénalise les crédits courts sans base statistique. **Pistes** : (a) limiter `duree_implicite` à l'intervalle vu en entraînement (8 à 45) avant prédiction et le documenter ; (b) retirer `duree_implicite` et ne garder que les ratios ; (c) refuser de scorer hors domaine et renvoyer vers une décision manuelle.
2. **Changement de domaine** : le modèle est appris sur Home Credit (crédit à la consommation, autre pays). C'est assumé dans le mémoire, mais à rappeler clairement au jury. Prévoir un **ré-étalonnage** (calibration isotonique) dès que les premiers remboursements réels seront disponibles.
3. **Hypothèse d'unité** : l'application calcule les ratios avec le revenu **mensuel**. Les distributions d'entraînement (médiane crédit/revenu 3,5, mensualité/revenu 0,17, 20,7 échéances) sont cohérentes avec un revenu et une mensualité de même période. Cette hypothèse mérite une phrase dans le mémoire.
4. **Explicabilité par dossier** : XGBoost fournit les contributions SHAP sans dépendance supplémentaire (`booster.predict(DMatrix, pred_contribs=True)`). Les enregistrer dans `score.facteurs` permettrait d'afficher « ce qui fait monter / baisser le risque » pour chaque client, ce qui tiendrait la promesse du site.
5. **Seuil** : `seuil_defaut` vaut 0,151 en base (0,15 dans le code par défaut). C'est cohérent, mais il faut tracer qui l'a modifié et quand (la date est présente, l'auteur reste à vérifier).
6. **Suivi du modèle** : ajouter un tableau de suivi (taux d'acceptation, défaut observé par tranche de score, dérive des variables) sur le DWH existant.

---

## 5. Données et cohérence fonctionnelle

- **Produits** : la base contient MICRO (50 000 à 1 000 000, 3 à 12 mois), PME (500 000 à 5 000 000, 6 à 24 mois) et SALARIE (100 000 à 2 000 000, 6 à 24 mois). Le site présente quatre autres produits, avec d'autres plafonds. **Une seule source de vérité est nécessaire** : soit créer les quatre produits en base (migration Alembic) et faire lire la page « Nos produits » depuis `/produits`, soit aligner le texte du site sur la base.
- **Dossiers** : 1 506 clients, 1 505 demandes (869 en remboursement, 315 soldées, 215 refusées, 43 en contentieux). Seuls les 50 derniers dossiers sont visibles dans la liste.
- **Score périmé** : correctement géré quand le dossier, le client ou la profession changent (`donnees_modifiees_le`).
- **Accord modifié** : le montant est contrôlé par rapport au produit, mais aucun score n'est recalculé pour ce montant. Il faudrait calculer et enregistrer la probabilité de défaut et l'endettement du montant accordé, puis les afficher au directeur avant validation.

---

## 6. Front

| Contrôle | Résultat |
|---|---|
| Build | ✅ 448 Ko de JS (129 Ko gzip), 66 Ko de CSS |
| Lint (oxlint) | 18 avertissements, aucune erreur : 11 `set-state-in-effect`, 5 `purity` (`new Date()` pendant le rendu), 2 `only-export-components` |
| Accessibilité | `aria-*` sur les menus, carrousel, pagination ; `prefers-reduced-motion` respecté ; **`lang="en"` à corriger en `lang="fr"`** |
| Fichiers morts | `Carrousel.jsx`, scène `SceneElevage`, `assets/hero.png`, `react.svg`, `vite.svg` ; `ancien.css` encore utilisé par 8 éléments |
| Performances | un seul bundle : découper par route avec `React.lazy` (pages du personnel, rapports, assistant) pour alléger la page d'accueil |
| Configuration | `VITE_API_URL` correctement utilisé ; ajouter un `.env.example` côté front |

---

## 7. Optimisations recommandées (ordre conseillé)

1. Générer une `SECRET_KEY` longue et ajouter le contrôle au démarrage.
2. Aligner les produits entre la base et le site (migration + lecture via l'API).
3. Traiter les durées courtes dans le modèle (bornage documenté ou retrait de `duree_implicite`).
4. Pagination côté API (`limite`, `decalage`, et un en-tête `X-Total-Count`), branchée sur le composant `Pagination` existant.
5. Contributions SHAP par dossier, affichées dans la fiche dossier.
6. Recalcul du risque pour un accord modifié.
7. Suite de tests `pytest` : règles de validation, calcul des mensualités et du calendrier, `suggerer_montant`, matrice des rôles (avec une base de test).
8. Révocation des jetons, temps constant à la connexion, verrou sur les paiements.
9. Front : `lang="fr"`, nettoyage des fichiers morts, découpage du bundle, correction des avertissements de lint.

---

## 8. Limites de cet audit

- Aucune écriture en base : la création de dossier, le scoring, la décision, le décaissement et le paiement de bout en bout n'ont pas été rejoués. Il faudrait une base de test dédiée.
- Les pages internes du front (personnel, admin, client) n'ont pas été vues à l'écran, faute de compte de test.
- Les jetons utilisés pour la matrice des rôles ont été générés localement avec la clé de l'application, sans mot de passe.
- L'assistant (classifieur d'intentions), l'ETL / DWH, les rapports Excel/PDF et Metabase n'ont été que survolés.

---

## 9. Suivi des corrections

| Date | Constat | Correction | Vérification |
|---|---|---|---|
| 11/11/2026 | `SECRET_KEY` de 9 octets | Nouvelle clé aléatoire de 64 octets dans `.env` ; `app/security.py` refuse de démarrer sous 32 octets ; `.env.example` explique comment générer la clé | l'API répond, un jeton signé avec une autre clé est refusé (401), plus d'avertissement PyJWT |
| 11/11/2026 | Produits du site absents de la base | Migration `b3f1c2a4d5e6` : ajout de COMMERCE (24 %), ARTISAN (22 %), AGRICOLE (20 %), EQUIPEMENT (18 %) aux montants et durées du site ; MICRO, PME et SALARIE restent actifs ; `app/seed.py` mis à jour | `/produits` renvoie les 7 produits ; 25 000 000 FCFA sur 60 mois accepté pour ARTISAN, montants et durées hors plage refusés |

Effets à connaître : les sessions ouvertes avant le changement de clé sont invalidées (il faut se reconnecter). Les rapports issus de l'entrepôt ne verront les nouveaux produits qu'après le prochain chargement de l'ETL.

---

## 10. Approfondissement : l'effet de la durée dans le modèle (11/11/2026)

Le constat du § 4.1 était incomplet. Une partie de l'écart (6 mois plus risqué que 12 mois) venait simplement d'une mensualité trop lourde pour le revenu, ce qui est légitime. En revanche, **à mensualité égale (20 % du revenu)**, le modèle v3 donne :

| Durée | 3 m | 6 m | 9 m | 12 m | 18 m | 24 m | 36 m | 60 m |
|---|---|---|---|---|---|---|---|---|
| v3 en service | 15,2 % | 15,9 % | 16,0 % | **10,9 %** | **26,0 %** | 21,5 % | 15,9 % | 17,3 % |

Ce profil en dents de scie vient de la variable `duree_implicite` (montant / mensualité), telle qu'elle se présente dans Home Credit : taux de défaut de 4,5 % pour 10 à 12 échéances, mais de 12,7 % pour 12 à 15 échéances. C'est vraisemblablement un effet de la gamme de produits de Home Credit, sans lien avec la microfinance sénégalaise.

### Essais réalisés (modèles d'essai, le modèle en service n'a pas été modifié)

| Variante | AUC test | PR-AUC | KS | Brier | Profil selon la durée |
|---|---|---|---|---|---|
| v3 réentraîné (référence) | 0,693 | 0,174 | 0,284 | 0,0733 | en dents de scie |
| A : sans `duree_implicite` | 0,628 | 0,132 | 0,188 | 0,0752 | régulier, de 14,8 % à 22,8 % |
| B : `duree_implicite` croissante (monotone) | 0,636 | 0,136 | 0,199 | 0,0751 | régulier, de 9,3 % à 22,9 % |

### Lecture
- **Environ 0,06 point d'AUC du modèle v3 repose sur ce motif de durée** propre à Home Credit. Sans lui, le modèle reste meilleur que le hasard, mais nettement moins discriminant.
- Ce gain risque de ne pas se transposer : il récompense ou pénalise des durées (12 mois contre 18 mois) pour des raisons qui tiennent au jeu de données d'origine.

### Options (décision méthodologique à prendre)
1. **Garder v3** et documenter la limite dans le mémoire, avec une règle de prudence : signaler au directeur les dossiers dont la durée relève d'une zone sensible.
2. **Passer à la variante B** (v4) : le comportement est cohérent (plus c'est long, plus c'est risqué, à mensualité égale) et l'AUC tombe à 0,636. Il faut alors mettre à jour les chiffres du mémoire.
3. **Passer à la variante A** (v4) : c'est le modèle le plus simple à justifier, avec une AUC de 0,628.

### Décision retenue : variante B, modèle v4 (11/11/2026)

**Changements**
- `src/modeling.py` : `duree_implicite` est ajoutée aux variables à effet croissant ; hyperparamètres réglés à nouveau sur la validation avec arrêt anticipé (profondeur 3, 551 arbres, taux 0,03 ; profondeurs testées : 3 → 0,6424, 4 → 0,6417, 5 → 0,6411, 6 → 0,6406).
- `models/xgb_home_credit_v4.joblib` : nouveau modèle (le fichier v3 est conservé).
- `app/scoring.py` : `VERSION_MODELE = "xgb_home_credit_v4"`. Les scores déjà enregistrés gardent la mention `v3`.

**Résultats sur le test (consulté une seule fois pour v4)**

| Mesure | v3 | v4 |
|---|---|---|
| AUC | 0,693 | 0,642 |
| PR-AUC | 0,174 | 0,139 |
| KS | 0,284 | 0,203 |
| Brier (référence 0,0765) | 0,0733 | 0,0749 |
| Plage des scores | 0,2 % à 55,5 % | 0,4 % à 37,5 % |
| Part des dossiers au-dessus de 15 % | 12,5 % | 7,3 % |

Note : l'AUC de v3 mesurée ici (0,693) diffère légèrement de celle du notebook (0,698) ; le fichier de données traité a probablement été régénéré depuis.

**Calibration v4** : écart inférieur à 0,5 point par décile (décile le plus risqué : 16,9 % prévus, 17,5 % observés).

**Équité v4** (seuil 15 %) : taux d'acceptation de 94,7 % pour les femmes et de 88,8 % pour les hommes, soit un rapport de 0,94 (contre 0,92 pour v3) ; l'AUC est proche entre les sexes (0,638 et 0,630). Le risque des diplômés du supérieur est surestimé (7,6 % prévus pour 5,5 % observés).

**Comportement selon la durée** (mensualité = 20 % du revenu) : 7,1 % de 3 à 9 mois, 7,6 % à 12 mois, 13,9 % de 18 à 60 mois. Le profil est désormais croissant, et le risque augmente toujours avec le montant.

**Conséquences pour la politique de crédit**
- Avec le même seuil (15,1 %), moins de dossiers dépassent le seuil (7,3 % contre 12,5 %) : le modèle accepte davantage. Le seuil est un paramètre du directeur ; il faudra peut-être le revoir (un seuil de 12 % donnerait un niveau de sélection proche de v3, à vérifier).
- Le palier entre 12 et 18 mois reste marqué : c'est la façon dont les arbres découpent la variable, et il reste cohérent (croissant).

**À mettre à jour dans le mémoire** : le tableau des résultats finaux, la calibration, l'audit d'équité et l'explication des variables (SHAP) du notebook 03, ainsi que la justification du choix de v4 (motif de durée propre à Home Credit, voir plus haut).
