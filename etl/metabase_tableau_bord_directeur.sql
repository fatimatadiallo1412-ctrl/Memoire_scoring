-- Tableau de bord du directeur (Metabase, tableau n° 2) : copie de référence des requêtes, état du 11/11/2026.
-- La configuration elle-même (mise en page, couleurs, titres d'axes) est stockée dans Metabase.
--
-- Filtres du tableau, tous « Modifiables » dans l'intégration :
--   Agence  -> {{agence}}  : filtre de champ sur dwh.dim_agence.nom
--   Produit -> {{produit}} : filtre de champ sur dwh.dim_produit.libelle
--   Date    -> {{periode}} : filtre de champ sur dwh.dim_temps.date (date de dépôt, de décaissement ou de paiement)
-- Les tables sont écrites en entier (sans alias) : Metabase remplace {{agence}} par « dwh.dim_agence.nom = ... ».
-- Les indicateurs du portefeuille en cours (PAR, encours, recouvrement, impayés) n'ont pas de filtre de date :
-- ils décrivent la situation à ce jour.
--
-- Définitions retenues
--   PAR 30 / PAR 90 : capital restant dû des crédits en retard de plus de 30 / 90 jours, rapporté au capital
--                     restant dû total des crédits en cours (norme prudentielle BCEAO des SFD : 3 %).
--   Recouvrement    : sommes payées / sommes dues, sur les seules échéances arrivées à terme.
--   Taux d'accord   : demandes accordées (avec ou sans modification) / demandes décidées.
--
-- Toutes les requêtes reprennent les mêmes jointures :
--   JOIN dwh.dim_agence  ON dwh.dim_agence.agence_key   = dwh.<fait>.agence_key
--   JOIN dwh.dim_produit ON dwh.dim_produit.produit_key = dwh.<fait>.produit_key
--   JOIN dwh.dim_temps   ON dwh.dim_temps.date_key      = dwh.<fait>.<clé de date>   (si filtre de période)
-- et se terminent par les filtres optionnels :
--   [[AND {{periode}}]] [[AND {{agence}}]] [[AND {{produit}}]]

-- =====================================================================================================
-- Onglet ACTIVITÉ
-- =====================================================================================================

-- Q69 Demandes reçues (indicateur)
SELECT COUNT(*) AS demandes
FROM dwh.fait_demande
JOIN dwh.dim_temps   ON dwh.dim_temps.date_key      = dwh.fait_demande.date_demande_key
JOIN dwh.dim_agence  ON dwh.dim_agence.agence_key   = dwh.fait_demande.agence_key
JOIN dwh.dim_produit ON dwh.dim_produit.produit_key = dwh.fait_demande.produit_key
WHERE 1 = 1
[[AND {{periode}}]]
[[AND {{agence}}]]
[[AND {{produit}}]];

-- Q70 Taux d'accord (indicateur, %)
SELECT ROUND(100.0 * SUM(dwh.fait_demande.est_accordee) / NULLIF(SUM(dwh.fait_demande.est_decidee), 0), 1) AS taux_accord
FROM dwh.fait_demande
JOIN dwh.dim_temps   ON dwh.dim_temps.date_key      = dwh.fait_demande.date_demande_key
JOIN dwh.dim_agence  ON dwh.dim_agence.agence_key   = dwh.fait_demande.agence_key
JOIN dwh.dim_produit ON dwh.dim_produit.produit_key = dwh.fait_demande.produit_key
WHERE 1 = 1
[[AND {{periode}}]]
[[AND {{agence}}]]
[[AND {{produit}}]];

-- Q71 Montant décaissé (indicateur, FCFA)
SELECT SUM(dwh.fait_credit.montant_decaisse) AS montant
FROM dwh.fait_credit
JOIN dwh.dim_temps   ON dwh.dim_temps.date_key      = dwh.fait_credit.date_decaissement_key
JOIN dwh.dim_agence  ON dwh.dim_agence.agence_key   = dwh.fait_credit.agence_key
JOIN dwh.dim_produit ON dwh.dim_produit.produit_key = dwh.fait_credit.produit_key
WHERE 1 = 1
[[AND {{periode}}]]
[[AND {{agence}}]]
[[AND {{produit}}]];

-- Q50 Délai moyen de décision (indicateur, jours)
SELECT ROUND(AVG(dwh.fait_demande.delai_decision_jours), 1) AS delai
FROM dwh.fait_demande
JOIN dwh.dim_temps   ON dwh.dim_temps.date_key      = dwh.fait_demande.date_demande_key
JOIN dwh.dim_agence  ON dwh.dim_agence.agence_key   = dwh.fait_demande.agence_key
JOIN dwh.dim_produit ON dwh.dim_produit.produit_key = dwh.fait_demande.produit_key
WHERE dwh.fait_demande.est_decidee = 1
[[AND {{periode}}]]
[[AND {{agence}}]]
[[AND {{produit}}]];

-- Q51 Demandes par mois (courbe ; le dernier mois est en cours)
SELECT dwh.dim_temps.annee_mois AS mois, COUNT(*) AS demandes
FROM dwh.fait_demande
JOIN dwh.dim_temps   ON dwh.dim_temps.date_key      = dwh.fait_demande.date_demande_key
JOIN dwh.dim_agence  ON dwh.dim_agence.agence_key   = dwh.fait_demande.agence_key
JOIN dwh.dim_produit ON dwh.dim_produit.produit_key = dwh.fait_demande.produit_key
WHERE 1 = 1
[[AND {{periode}}]]
[[AND {{agence}}]]
[[AND {{produit}}]]
GROUP BY 1 ORDER BY 1;

-- Q53 Montants décaissés par mois (barres)
SELECT dwh.dim_temps.annee_mois AS mois, SUM(dwh.fait_credit.montant_decaisse) AS decaisse_fcfa
FROM dwh.fait_credit
JOIN dwh.dim_temps   ON dwh.dim_temps.date_key      = dwh.fait_credit.date_decaissement_key
JOIN dwh.dim_agence  ON dwh.dim_agence.agence_key   = dwh.fait_credit.agence_key
JOIN dwh.dim_produit ON dwh.dim_produit.produit_key = dwh.fait_credit.produit_key
WHERE 1 = 1
[[AND {{periode}}]]
[[AND {{agence}}]]
[[AND {{produit}}]]
GROUP BY 1 ORDER BY 1;

-- Q52 Dossiers par statut (barres horizontales, libellés en français)
SELECT CASE dwh.fait_demande.statut WHEN 'en_remboursement' THEN 'En remboursement' WHEN 'solde' THEN 'Soldé' WHEN 'refuse' THEN 'Refusé'
  WHEN 'contentieux' THEN 'Contentieux' WHEN 'ajourne' THEN 'Ajourné' WHEN 'accorde' THEN 'Accordé (à décaisser)'
  WHEN 'accorde_modifie' THEN 'Accordé modifié (à décaisser)' WHEN 'soumis_decision' THEN 'En attente de décision'
  WHEN 'score' THEN 'Scoré' WHEN 'instruit' THEN 'Instruit' WHEN 'complet' THEN 'Complet' WHEN 'brouillon' THEN 'Brouillon'
  ELSE dwh.fait_demande.statut END AS statut, COUNT(*) AS dossiers
FROM dwh.fait_demande
JOIN dwh.dim_temps   ON dwh.dim_temps.date_key      = dwh.fait_demande.date_demande_key
JOIN dwh.dim_agence  ON dwh.dim_agence.agence_key   = dwh.fait_demande.agence_key
JOIN dwh.dim_produit ON dwh.dim_produit.produit_key = dwh.fait_demande.produit_key
WHERE 1 = 1
[[AND {{periode}}]]
[[AND {{agence}}]]
[[AND {{produit}}]]
GROUP BY 1 ORDER BY 2 DESC;

-- Q54 Activité par gestionnaire (barres empilées : accordées, refusées, en cours ou ajournées)
SELECT dwh.dim_agent.nom_complet AS gestionnaire,
       SUM(dwh.fait_demande.est_accordee) AS accordees,
       SUM(dwh.fait_demande.est_refusee) AS refusees,
       COUNT(*) - SUM(dwh.fait_demande.est_accordee) - SUM(dwh.fait_demande.est_refusee) AS autres
FROM dwh.fait_demande
JOIN dwh.dim_agent   ON dwh.dim_agent.agent_key     = dwh.fait_demande.agent_key
JOIN dwh.dim_temps   ON dwh.dim_temps.date_key      = dwh.fait_demande.date_demande_key
JOIN dwh.dim_agence  ON dwh.dim_agence.agence_key   = dwh.fait_demande.agence_key
JOIN dwh.dim_produit ON dwh.dim_produit.produit_key = dwh.fait_demande.produit_key
WHERE 1 = 1
[[AND {{periode}}]]
[[AND {{agence}}]]
[[AND {{produit}}]]
GROUP BY 1 ORDER BY COUNT(*) DESC;

-- Q48 Paiements reçus par mode
SELECT CASE dwh.fait_paiement.mode WHEN 'especes' THEN 'Espèces' WHEN 'mobile_money' THEN 'Mobile money' WHEN 'virement' THEN 'Virement' ELSE dwh.fait_paiement.mode END AS mode,
       SUM(dwh.fait_paiement.montant) AS montant
FROM dwh.fait_paiement
JOIN dwh.dim_temps   ON dwh.dim_temps.date_key      = dwh.fait_paiement.date_paiement_key
JOIN dwh.dim_agence  ON dwh.dim_agence.agence_key   = dwh.fait_paiement.agence_key
JOIN dwh.dim_produit ON dwh.dim_produit.produit_key = dwh.fait_paiement.produit_key
WHERE 1 = 1
[[AND {{periode}}]]
[[AND {{agence}}]]
[[AND {{produit}}]]
GROUP BY 1 ORDER BY 2 DESC;

-- =====================================================================================================
-- Onglet RISQUE
-- =====================================================================================================

-- Q72 PAR 30 (indicateur, %)
SELECT ROUND(100.0 * SUM(CASE WHEN dwh.fait_credit.est_retard_30 = 1 THEN dwh.fait_credit.capital_restant ELSE 0 END)
             / NULLIF(SUM(dwh.fait_credit.capital_restant), 0), 1) AS par_30
FROM dwh.fait_credit
JOIN dwh.dim_agence  ON dwh.dim_agence.agence_key   = dwh.fait_credit.agence_key
JOIN dwh.dim_produit ON dwh.dim_produit.produit_key = dwh.fait_credit.produit_key
WHERE dwh.fait_credit.est_solde = 0
[[AND {{agence}}]]
[[AND {{produit}}]];

-- Q73 PAR 90 (indicateur, %) : même requête avec est_contentieux à la place de est_retard_30.

-- Q74 Encours de crédit (indicateur, FCFA)
SELECT SUM(dwh.fait_credit.capital_restant) AS encours
FROM dwh.fait_credit
JOIN dwh.dim_agence  ON dwh.dim_agence.agence_key   = dwh.fait_credit.agence_key
JOIN dwh.dim_produit ON dwh.dim_produit.produit_key = dwh.fait_credit.produit_key
WHERE dwh.fait_credit.est_solde = 0
[[AND {{agence}}]]
[[AND {{produit}}]];

-- Q75 Taux de recouvrement (indicateur, %) ; Q61 : même calcul, groupé par dwh.dim_agence.nom
SELECT ROUND(100.0 * SUM(dwh.fait_echeance.montant_paye) / NULLIF(SUM(dwh.fait_echeance.montant_du), 0), 1) AS recouvrement
FROM dwh.fait_echeance
JOIN dwh.dim_temps   ON dwh.dim_temps.date_key      = dwh.fait_echeance.date_echeance_key
JOIN dwh.dim_agence  ON dwh.dim_agence.agence_key   = dwh.fait_echeance.agence_key
JOIN dwh.dim_produit ON dwh.dim_produit.produit_key = dwh.fait_echeance.produit_key
WHERE dwh.dim_temps.date <= CURRENT_DATE
[[AND {{agence}}]]
[[AND {{produit}}]];

-- Q47 Évolution du PAR 30 (courbe, ligne d'objectif à 3 %)
SELECT dwh.dim_temps.annee_mois AS mois,
       ROUND(100.0 * SUM(CASE WHEN dwh.fait_portefeuille_mensuel.est_retard_30 = 1 THEN dwh.fait_portefeuille_mensuel.capital_restant ELSE 0 END)
             / NULLIF(SUM(dwh.fait_portefeuille_mensuel.capital_restant), 0), 1) AS par_30
FROM dwh.fait_portefeuille_mensuel
JOIN dwh.dim_temps   ON dwh.dim_temps.date_key      = dwh.fait_portefeuille_mensuel.date_key
JOIN dwh.dim_agence  ON dwh.dim_agence.agence_key   = dwh.fait_portefeuille_mensuel.agence_key
JOIN dwh.dim_produit ON dwh.dim_produit.produit_key = dwh.fait_portefeuille_mensuel.produit_key
WHERE 1 = 1
[[AND {{periode}}]]
[[AND {{agence}}]]
[[AND {{produit}}]]
GROUP BY 1 ORDER BY 1;

-- Q55 PAR 30 et PAR 90 par agence (barres, ligne d'objectif à 3 %)
SELECT dwh.dim_agence.nom AS agence,
       ROUND(100.0 * SUM(CASE WHEN dwh.fait_credit.est_retard_30 = 1 THEN dwh.fait_credit.capital_restant ELSE 0 END)
             / NULLIF(SUM(dwh.fait_credit.capital_restant), 0), 1) AS par_30,
       ROUND(100.0 * SUM(CASE WHEN dwh.fait_credit.est_contentieux = 1 THEN dwh.fait_credit.capital_restant ELSE 0 END)
             / NULLIF(SUM(dwh.fait_credit.capital_restant), 0), 1) AS par_90
FROM dwh.fait_credit
JOIN dwh.dim_agence  ON dwh.dim_agence.agence_key   = dwh.fait_credit.agence_key
JOIN dwh.dim_produit ON dwh.dim_produit.produit_key = dwh.fait_credit.produit_key
WHERE dwh.fait_credit.est_solde = 0
[[AND {{agence}}]]
[[AND {{produit}}]]
GROUP BY 1 ORDER BY 2 DESC;

-- Q56 PAR 30 par produit : même calcul que Q55 (par_30 seul), groupé par dwh.dim_produit.libelle.

-- Q63 Capital en cours selon l'ancienneté du retard
SELECT CASE WHEN dwh.fait_credit.jours_retard_max = 0  THEN '1. À jour'
            WHEN dwh.fait_credit.jours_retard_max <= 30 THEN '2. 1 à 30 jours'
            WHEN dwh.fait_credit.jours_retard_max <= 90 THEN '3. 31 à 90 jours'
            ELSE '4. Plus de 90 jours' END AS tranche,
       COUNT(*) AS credits, SUM(dwh.fait_credit.capital_restant) AS capital_fcfa
FROM dwh.fait_credit
JOIN dwh.dim_agence  ON dwh.dim_agence.agence_key   = dwh.fait_credit.agence_key
JOIN dwh.dim_produit ON dwh.dim_produit.produit_key = dwh.fait_credit.produit_key
WHERE dwh.fait_credit.est_solde = 0
[[AND {{agence}}]]
[[AND {{produit}}]]
GROUP BY 1 ORDER BY 1;

-- Q62 Dix plus gros impayés (tableau)
SELECT dwh.dim_client.code_client AS client, dwh.dim_agent.nom_complet AS gestionnaire, dwh.dim_agence.nom AS agence,
       dwh.fait_credit.jours_retard_max AS jours_retard, dwh.fait_credit.montant_en_retard, dwh.fait_credit.capital_restant
FROM dwh.fait_credit
JOIN dwh.dim_client  ON dwh.dim_client.client_key   = dwh.fait_credit.client_key
JOIN dwh.dim_agent   ON dwh.dim_agent.agent_key     = dwh.fait_credit.agent_key
JOIN dwh.dim_agence  ON dwh.dim_agence.agence_key   = dwh.fait_credit.agence_key
JOIN dwh.dim_produit ON dwh.dim_produit.produit_key = dwh.fait_credit.produit_key
WHERE dwh.fait_credit.est_solde = 0 AND dwh.fait_credit.montant_en_retard > 0
[[AND {{agence}}]]
[[AND {{produit}}]]
ORDER BY dwh.fait_credit.montant_en_retard DESC LIMIT 10;

-- =====================================================================================================
-- Onglet AIDE À LA DÉCISION
-- =====================================================================================================

-- Q49 Décisions conformes au modèle (anneau)
SELECT CASE WHEN dwh.fait_demande.concordance THEN 'Conforme' ELSE 'Contraire (motivée)' END AS issue, COUNT(*) AS dossiers
FROM dwh.fait_demande
JOIN dwh.dim_temps   ON dwh.dim_temps.date_key      = dwh.fait_demande.date_demande_key
JOIN dwh.dim_agence  ON dwh.dim_agence.agence_key   = dwh.fait_demande.agence_key
JOIN dwh.dim_produit ON dwh.dim_produit.produit_key = dwh.fait_demande.produit_key
WHERE dwh.fait_demande.concordance IS NOT NULL
[[AND {{periode}}]]
[[AND {{agence}}]]
[[AND {{produit}}]]
GROUP BY 1 ORDER BY 1;

-- Q57 Recommandation du modèle et décision du directeur (barres empilées)
SELECT CASE dwh.fait_demande.recommandation WHEN 'accord' THEN '1. Accord' WHEN 'accord_reduit' THEN '2. Accord réduit'
            WHEN 'refus' THEN '3. Refus' ELSE 'Non scoré' END AS recommandation,
       CASE dwh.fait_demande.decision WHEN 'accorder' THEN 'Accordé' WHEN 'accorder_modifie' THEN 'Accordé modifié'
            WHEN 'refuser' THEN 'Refusé' WHEN 'ajourner' THEN 'Ajourné' ELSE 'En attente' END AS decision,
       COUNT(*) AS dossiers
FROM dwh.fait_demande
JOIN dwh.dim_temps   ON dwh.dim_temps.date_key      = dwh.fait_demande.date_demande_key
JOIN dwh.dim_agence  ON dwh.dim_agence.agence_key   = dwh.fait_demande.agence_key
JOIN dwh.dim_produit ON dwh.dim_produit.produit_key = dwh.fait_demande.produit_key
WHERE dwh.fait_demande.recommandation IS NOT NULL
[[AND {{periode}}]]
[[AND {{agence}}]]
[[AND {{produit}}]]
GROUP BY 1, 2 ORDER BY 1, 2;

-- Q76 Répartition des dossiers selon le risque prévu
SELECT CASE WHEN dwh.fait_demande.p_defaut < 0.04 THEN '1. Moins de 4 %' WHEN dwh.fait_demande.p_defaut < 0.08 THEN '2. 4 à 8 %'
            WHEN dwh.fait_demande.p_defaut < 0.12 THEN '3. 8 à 12 %' WHEN dwh.fait_demande.p_defaut < 0.16 THEN '4. 12 à 16 %'
            ELSE '5. 16 % et plus' END AS tranche, COUNT(*) AS dossiers
FROM dwh.fait_demande
JOIN dwh.dim_temps   ON dwh.dim_temps.date_key      = dwh.fait_demande.date_demande_key
JOIN dwh.dim_agence  ON dwh.dim_agence.agence_key   = dwh.fait_demande.agence_key
JOIN dwh.dim_produit ON dwh.dim_produit.produit_key = dwh.fait_demande.produit_key
WHERE dwh.fait_demande.p_defaut IS NOT NULL
[[AND {{periode}}]]
[[AND {{agence}}]]
[[AND {{produit}}]]
GROUP BY 1 ORDER BY 1;

-- Q77 Retards observés selon le risque prévu (validation du modèle en production)
SELECT CASE WHEN dwh.fait_demande.p_defaut < 0.04 THEN '1. Moins de 4 %' WHEN dwh.fait_demande.p_defaut < 0.08 THEN '2. 4 à 8 %'
            WHEN dwh.fait_demande.p_defaut < 0.12 THEN '3. 8 à 12 %' WHEN dwh.fait_demande.p_defaut < 0.16 THEN '4. 12 à 16 %'
            ELSE '5. 16 % et plus' END AS tranche, COUNT(*) AS credits,
       ROUND(100.0 * SUM(dwh.fait_credit.est_retard_30) / NULLIF(COUNT(*), 0), 1) AS taux_retard_30
FROM dwh.fait_credit
JOIN dwh.fait_demande ON dwh.fait_demande.demande_key = dwh.fait_credit.demande_key
JOIN dwh.dim_temps   ON dwh.dim_temps.date_key      = dwh.fait_credit.date_decaissement_key
JOIN dwh.dim_agence  ON dwh.dim_agence.agence_key   = dwh.fait_credit.agence_key
JOIN dwh.dim_produit ON dwh.dim_produit.produit_key = dwh.fait_credit.produit_key
WHERE dwh.fait_demande.p_defaut IS NOT NULL
[[AND {{periode}}]]
[[AND {{agence}}]]
[[AND {{produit}}]]
GROUP BY 1 ORDER BY 1;

-- Q58 Montant accordé / montant demandé (indicateur, %)
SELECT ROUND(100.0 * SUM(dwh.fait_demande.montant_accorde) / NULLIF(SUM(dwh.fait_demande.montant_demande), 0), 1) AS pct_accorde
FROM dwh.fait_demande
JOIN dwh.dim_temps   ON dwh.dim_temps.date_key      = dwh.fait_demande.date_demande_key
JOIN dwh.dim_agence  ON dwh.dim_agence.agence_key   = dwh.fait_demande.agence_key
JOIN dwh.dim_produit ON dwh.dim_produit.produit_key = dwh.fait_demande.produit_key
WHERE dwh.fait_demande.est_accordee = 1
[[AND {{periode}}]]
[[AND {{agence}}]]
[[AND {{produit}}]];

-- Q59 Taux d'accord selon l'ancienneté de l'activité (modèle commun aux taux d'accord, voir aussi Q46, Q78 à Q80)
SELECT dwh.dim_client.tranche_anciennete AS groupe, COUNT(*) AS demandes_decidees,
       ROUND(100.0 * SUM(dwh.fait_demande.est_accordee) / NULLIF(COUNT(*), 0), 1) AS taux_accord
FROM dwh.fait_demande
JOIN dwh.dim_client  ON dwh.dim_client.client_key   = dwh.fait_demande.client_key
JOIN dwh.dim_temps   ON dwh.dim_temps.date_key      = dwh.fait_demande.date_demande_key
JOIN dwh.dim_agence  ON dwh.dim_agence.agence_key   = dwh.fait_demande.agence_key
JOIN dwh.dim_produit ON dwh.dim_produit.produit_key = dwh.fait_demande.produit_key
WHERE dwh.fait_demande.est_decidee = 1
[[AND {{periode}}]]
[[AND {{agence}}]]
[[AND {{produit}}]]
GROUP BY 1
ORDER BY CASE dwh.dim_client.tranche_anciennete WHEN '< 1 an' THEN 1 WHEN '1 à 3 ans' THEN 2 WHEN '3 à 6 ans' THEN 3 ELSE 4 END;

-- =====================================================================================================
-- Onglet INCLUSION
-- =====================================================================================================

-- Q82 Crédits décaissés (indicateur)
SELECT COUNT(*) AS credits
FROM dwh.fait_credit
JOIN dwh.dim_temps   ON dwh.dim_temps.date_key      = dwh.fait_credit.date_decaissement_key
JOIN dwh.dim_agence  ON dwh.dim_agence.agence_key   = dwh.fait_credit.agence_key
JOIN dwh.dim_produit ON dwh.dim_produit.produit_key = dwh.fait_credit.produit_key
WHERE 1 = 1
[[AND {{periode}}]]
[[AND {{agence}}]]
[[AND {{produit}}]];

-- Q81 Part des femmes parmi les clients financés (indicateur, %)
SELECT ROUND(100.0 * SUM(CASE WHEN dwh.dim_client.sexe = 'F' THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0), 1) AS part_femmes
FROM dwh.fait_credit
JOIN dwh.dim_client  ON dwh.dim_client.client_key   = dwh.fait_credit.client_key
JOIN dwh.dim_temps   ON dwh.dim_temps.date_key      = dwh.fait_credit.date_decaissement_key
JOIN dwh.dim_agence  ON dwh.dim_agence.agence_key   = dwh.fait_credit.agence_key
JOIN dwh.dim_produit ON dwh.dim_produit.produit_key = dwh.fait_credit.produit_key
WHERE 1 = 1
[[AND {{periode}}]]
[[AND {{agence}}]]
[[AND {{produit}}]];

-- Q78 Taux d'accord par sexe       : modèle Q59, groupe = Femmes / Hommes (dwh.dim_client.sexe)
-- Q46 Taux d'accord par type de revenu : modèle Q59, groupe = dwh.dim_client.type_revenu (libellés en français)
-- Q79 Taux d'accord par tranche d'âge  : modèle Q59, groupe = dwh.dim_client.tranche_age
-- Q80 Taux d'accord par tranche de revenu : modèle Q59, groupe = dwh.dim_client.tranche_revenu

-- Q60 Taux de refus par agence
SELECT dwh.dim_agence.nom AS agence,
       ROUND(100.0 * SUM(dwh.fait_demande.est_refusee) / NULLIF(COUNT(*), 0), 1) AS taux_refus
FROM dwh.fait_demande
JOIN dwh.dim_temps   ON dwh.dim_temps.date_key      = dwh.fait_demande.date_demande_key
JOIN dwh.dim_agence  ON dwh.dim_agence.agence_key   = dwh.fait_demande.agence_key
JOIN dwh.dim_produit ON dwh.dim_produit.produit_key = dwh.fait_demande.produit_key
WHERE dwh.fait_demande.est_decidee = 1
[[AND {{periode}}]]
[[AND {{agence}}]]
[[AND {{produit}}]]
GROUP BY 1 ORDER BY 2 DESC;
