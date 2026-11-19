# Diagrammes UML et schémas de la plateforme (mis à jour le 19/11/2026)

Chaque diagramme existe en trois fichiers : la source modifiable (`.mmd`, syntaxe Mermaid), l'image vectorielle (`.svg`) et l'image pour le mémoire (`.png`, haute résolution).

Pour régénérer les images après une modification :

```bash
.venv/bin/python docs/uml/rendre.py              # tous les diagrammes
.venv/bin/python docs/uml/rendre.py 03b_sequence_decision   # un seul
```

Le rendu n'utilise pas Internet : Mermaid 11.12 est lu dans la copie fournie avec RStudio/Quarto (variable `MERMAID_JS` pour en indiquer une autre) et dessiné par Playwright.

## Liste

| Fichier | Diagramme | Par rapport à la version du 09/11 |
|---|---|---|
| `01a_cas_utilisation_global` | Cas d'utilisation : vue d'ensemble | Ajout du visiteur (site public, contact, mot de passe oublié) et du planificateur. L'administrateur n'a plus accès au pilotage ni à l'assistant (il n'accède à aucune donnée client). Ajout de la santé du modèle, des portefeuilles et des métiers à classer. |
| `01b_cas_utilisation_instruction_decision` | Cas d'utilisation : instruction et décision | **Nouveau.** Historique interne, explication par valeurs de Shapley, recommandations au client, simulation d'un accord modifié, motif communiqué au client. |
| `01c_cas_utilisation_pilotage_administration` | Cas d'utilisation : pilotage, administration, suivi | Paramètres de la politique, lien Metabase signé, affectation des portefeuilles, classement des métiers, réinitialisations, messages, santé du modèle, tâches programmées. |
| `01d_cas_utilisation_client` | Cas d'utilisation : espace client | Ajout : accès ouvert par l'agent, changement de mot de passe, suivi des demandes, motif et conseils après un refus. |
| `02_diagramme_classes` | Diagramme de classes (modèle du domaine) | **Nouveau.** Établi à partir des tables réelles (`ops`, `ml`, `audit`). |
| `03a_sequence_scoring` | Séquence : saisie et scoring | Modèle **v4**, seuil de 12 % (× 0,8 après incident régularisé), contributions de Shapley, recommandations au client, variables microfinance enregistrées, score périmé. |
| `03b_sequence_decision` | Séquence : instruction et décision | Simulation d'un accord modifié, risque recalculé, motif communiqué au client obligatoire pour un refus contraire au modèle. |
| `03c_sequence_decaissement` | Séquence : décaissement et paiement | Aperçu du décaissement avant validation ; date, mode et référence du décaissement. |
| `03d_sequence_assistant` | Séquence : assistant client | Inchangé sur le fond ; mention de l'assistant du personnel. |
| `03e_sequence_rappels` | Séquence : rappels | Inchangé sur le fond. |
| `03f_sequence_sante_modele` | Séquence : suivi du modèle | **Nouveau.** PSI corrigé du bruit, dérogations, performance sur les crédits mûrs, rapport mensuel ou à la demande. |
| `04a_activite_dossier` | Activité : cycle de vie d'un dossier | Recalcul du score si les données changent, ajournement puis nouvelle soumission, retour au client après un refus, note sur le statut contentieux. |
| `05_schema_etoile` | Entrepôt de données (constellation) | Structure inchangée (vérifiée sur la base le 19/11). Seules les colonnes principales sont affichées ; la liste complète est dans `etl/chargement_dwh.sql`. |
| `06_architecture` | Architecture générale | Interface React réelle (elle était « prévue »), modèle v4, planificateur (rappels et suivi), santé du modèle, schéma `ml` des scores et rapports. |

## Point à signaler dans le mémoire

Le statut **contentieux** figure dans le cycle de vie (`app/workflow.py`) et dans l'entrepôt, mais aucune action de l'application ne le pose : il n'existe que dans les données simulées (`simulation/rembourser.py`).
