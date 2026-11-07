-- Dimension temps : un jour par ligne, de 2024 à 2028
INSERT INTO dwh.dim_temps
SELECT to_char(d, 'YYYYMMDD')::int, d::date,
       extract(year FROM d), extract(quarter FROM d), extract(month FROM d),
       (ARRAY['janvier','février','mars','avril','mai','juin','juillet','août',
              'septembre','octobre','novembre','décembre'])[extract(month FROM d)::int],
       to_char(d, 'YYYY-MM'), extract(week FROM d), extract(day FROM d),
       extract(isodow FROM d),
       (ARRAY['lundi','mardi','mercredi','jeudi','vendredi','samedi','dimanche'])[extract(isodow FROM d)::int],
       extract(isodow FROM d) >= 6
FROM generate_series('2024-01-01'::date, '2028-12-31'::date, interval '1 day') AS d;

INSERT INTO dwh.dim_agence
SELECT id, code, nom, zone FROM ops.agence;

INSERT INTO dwh.dim_produit
SELECT id, code, libelle, taux_annuel, montant_min, montant_max, duree_min_mois, duree_max_mois
FROM ops.produit_credit;

INSERT INTO dwh.dim_agent
SELECT id, nom_complet, role::text, agence_id
FROM ops.utilisateur
WHERE role::text IN ('agent_credit', 'decideur', 'administrateur');

INSERT INTO dwh.dim_client
SELECT c.id, c.code_client, c.sexe,
       CASE WHEN a.age < 25 THEN '18-24 ans'
            WHEN a.age < 35 THEN '25-34 ans'
            WHEN a.age < 45 THEN '35-44 ans'
            WHEN a.age < 55 THEN '45-54 ans'
            ELSE '55 ans et plus' END,
       c.type_revenu, c.profession, c.situation_familiale, c.type_logement,
       CASE WHEN c.revenu_mensuel < 100000 THEN '< 100 000'
            WHEN c.revenu_mensuel < 200000 THEN '100 000 - 199 999'
            WHEN c.revenu_mensuel < 400000 THEN '200 000 - 399 999'
            ELSE '400 000 et plus' END,
       CASE WHEN c.anciennete_activite_mois < 12 THEN '< 1 an'
            WHEN c.anciennete_activite_mois < 36 THEN '1 à 3 ans'
            WHEN c.anciennete_activite_mois < 72 THEN '3 à 6 ans'
            ELSE '6 ans et +' END,
       c.nb_enfants, c.agence_id
FROM ops.client c
CROSS JOIN LATERAL (SELECT date_part('year', age(current_date, c.date_naissance)) AS age) a;

INSERT INTO dwh.fait_demande
SELECT d.id, d.numero,
       to_char(d.date_demande, 'YYYYMMDD')::int,
       CASE WHEN dec.id IS NULL THEN NULL ELSE to_char(dec.decide_le, 'YYYYMMDD')::int END,
       d.client_id, c.agence_id, d.produit_id, d.instructeur_id,
       d.statut::text, d.montant_demande, d.duree_mois,
       s.p_defaut, s.seuil_applique, s.recommandation,
       dec.decision::text, dec.montant_accorde, dec.duree_accordee, dec.concordance,
       CASE WHEN dec.id IS NULL THEN NULL ELSE (dec.decide_le::date - d.date_demande) END,
       1,
       (dec.id IS NOT NULL)::int,
       COALESCE(dec.decision::text IN ('accorder', 'accorder_modifie'), false)::int,
       COALESCE(dec.decision::text = 'refuser', false)::int
FROM ops.demande_credit d
JOIN ops.client c ON c.id = d.client_id
LEFT JOIN LATERAL (SELECT * FROM ml.score WHERE demande_id = d.id
                   ORDER BY calcule_le DESC LIMIT 1) s ON true
LEFT JOIN LATERAL (SELECT * FROM ops.decision WHERE demande_id = d.id
                   ORDER BY decide_le DESC LIMIT 1) dec ON true;