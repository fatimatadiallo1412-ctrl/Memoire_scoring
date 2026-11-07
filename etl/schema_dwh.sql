-- Entrepôt de données : schéma en étoile. Reconstruit à chaque exécution.
DROP SCHEMA IF EXISTS dwh CASCADE;
CREATE SCHEMA dwh;

CREATE TABLE dwh.dim_temps (
    date_key      INTEGER PRIMARY KEY,
    date          DATE NOT NULL UNIQUE,
    annee         SMALLINT NOT NULL,
    trimestre     SMALLINT NOT NULL,
    mois          SMALLINT NOT NULL,
    nom_mois      TEXT NOT NULL,
    annee_mois    TEXT NOT NULL,
    semaine       SMALLINT NOT NULL,
    jour          SMALLINT NOT NULL,
    jour_semaine  SMALLINT NOT NULL,
    nom_jour      TEXT NOT NULL,
    est_weekend   BOOLEAN NOT NULL
);

CREATE TABLE dwh.dim_agence (
    agence_key INTEGER PRIMARY KEY,
    code TEXT NOT NULL,
    nom TEXT NOT NULL,
    zone TEXT
);

CREATE TABLE dwh.dim_produit (
    produit_key INTEGER PRIMARY KEY,
    code TEXT NOT NULL,
    libelle TEXT NOT NULL,
    taux_annuel NUMERIC(5,2) NOT NULL,
    montant_min BIGINT NOT NULL,
    montant_max BIGINT NOT NULL,
    duree_min_mois INTEGER NOT NULL,
    duree_max_mois INTEGER NOT NULL
);

CREATE TABLE dwh.dim_agent (
    agent_key INTEGER PRIMARY KEY,
    nom_complet TEXT NOT NULL,
    role TEXT NOT NULL,
    agence_key INTEGER REFERENCES dwh.dim_agence
);

CREATE TABLE dwh.dim_client (
    client_key INTEGER PRIMARY KEY,
    code_client TEXT NOT NULL,
    sexe TEXT,                       -- suivi d'équité uniquement, jamais utilisé par le modèle
    tranche_age TEXT NOT NULL,
    type_revenu TEXT NOT NULL,
    profession TEXT,
    situation_familiale TEXT NOT NULL,
    type_logement TEXT NOT NULL,
    tranche_revenu TEXT NOT NULL,
    tranche_anciennete TEXT NOT NULL,
    nb_enfants INTEGER NOT NULL,
    agence_key INTEGER REFERENCES dwh.dim_agence
);

CREATE TABLE dwh.fait_demande (
    demande_key INTEGER PRIMARY KEY,
    numero TEXT NOT NULL,
    date_demande_key INTEGER NOT NULL REFERENCES dwh.dim_temps,
    date_decision_key INTEGER REFERENCES dwh.dim_temps,
    client_key INTEGER NOT NULL REFERENCES dwh.dim_client,
    agence_key INTEGER NOT NULL REFERENCES dwh.dim_agence,
    produit_key INTEGER NOT NULL REFERENCES dwh.dim_produit,
    agent_key INTEGER NOT NULL REFERENCES dwh.dim_agent,
    statut TEXT NOT NULL,
    montant_demande BIGINT NOT NULL,
    duree_demande INTEGER NOT NULL,
    p_defaut NUMERIC(7,6),
    seuil_applique NUMERIC(5,4),
    recommandation TEXT,
    decision TEXT,
    montant_accorde BIGINT,
    duree_accordee INTEGER,
    concordance BOOLEAN,
    delai_decision_jours INTEGER,
    nb_demandes SMALLINT NOT NULL DEFAULT 1,
    est_decidee SMALLINT NOT NULL,
    est_accordee SMALLINT NOT NULL,
    est_refusee SMALLINT NOT NULL
);

CREATE TABLE dwh.fait_credit (
    credit_key INTEGER PRIMARY KEY,
    demande_key INTEGER NOT NULL REFERENCES dwh.fait_demande,
    date_decaissement_key INTEGER NOT NULL REFERENCES dwh.dim_temps,
    client_key INTEGER NOT NULL REFERENCES dwh.dim_client,
    agence_key INTEGER NOT NULL REFERENCES dwh.dim_agence,
    produit_key INTEGER NOT NULL REFERENCES dwh.dim_produit,
    agent_key INTEGER NOT NULL REFERENCES dwh.dim_agent,
    statut TEXT NOT NULL,
    montant_decaisse BIGINT NOT NULL,
    mensualite BIGINT NOT NULL,
    taux_annuel NUMERIC(6,4) NOT NULL,
    duree_mois INTEGER NOT NULL,
    total_du BIGINT NOT NULL,
    total_paye BIGINT NOT NULL,
    reste_a_payer BIGINT NOT NULL,
    capital_restant BIGINT NOT NULL,
    nb_echeances_en_retard INTEGER NOT NULL,
    montant_en_retard BIGINT NOT NULL,
    jours_retard_max INTEGER NOT NULL,
    est_solde SMALLINT NOT NULL,
    est_retard_30 SMALLINT NOT NULL,
    est_contentieux SMALLINT NOT NULL
);

CREATE TABLE dwh.fait_echeance (
    echeance_key INTEGER PRIMARY KEY,
    credit_key INTEGER NOT NULL REFERENCES dwh.fait_credit,
    numero INTEGER NOT NULL,
    date_echeance_key INTEGER NOT NULL REFERENCES dwh.dim_temps,
    client_key INTEGER NOT NULL REFERENCES dwh.dim_client,
    agence_key INTEGER NOT NULL REFERENCES dwh.dim_agence,
    produit_key INTEGER NOT NULL REFERENCES dwh.dim_produit,
    montant_du BIGINT NOT NULL,
    capital BIGINT NOT NULL,
    interet BIGINT NOT NULL,
    montant_paye BIGINT NOT NULL,
    reste_du BIGINT NOT NULL,
    statut TEXT NOT NULL,
    jours_retard INTEGER NOT NULL
);

CREATE TABLE dwh.fait_paiement (
    paiement_key INTEGER PRIMARY KEY,
    credit_key INTEGER NOT NULL REFERENCES dwh.fait_credit,
    date_paiement_key INTEGER NOT NULL REFERENCES dwh.dim_temps,
    client_key INTEGER NOT NULL REFERENCES dwh.dim_client,
    agence_key INTEGER NOT NULL REFERENCES dwh.dim_agence,
    produit_key INTEGER NOT NULL REFERENCES dwh.dim_produit,
    agent_key INTEGER NOT NULL REFERENCES dwh.dim_agent,
    montant BIGINT NOT NULL,
    mode TEXT NOT NULL
);

CREATE TABLE dwh.fait_portefeuille_mensuel (
    credit_key INTEGER NOT NULL REFERENCES dwh.fait_credit,
    date_key INTEGER NOT NULL REFERENCES dwh.dim_temps,
    client_key INTEGER NOT NULL REFERENCES dwh.dim_client,
    agence_key INTEGER NOT NULL REFERENCES dwh.dim_agence,
    produit_key INTEGER NOT NULL REFERENCES dwh.dim_produit,
    capital_restant BIGINT NOT NULL,
    reste_a_payer BIGINT NOT NULL,
    jours_retard_max INTEGER NOT NULL,
    est_retard_30 SMALLINT NOT NULL,
    est_retard_90 SMALLINT NOT NULL,
    PRIMARY KEY (credit_key, date_key)
);

CREATE INDEX ix_fait_demande_date ON dwh.fait_demande (date_demande_key);
CREATE INDEX ix_fait_echeance_date ON dwh.fait_echeance (date_echeance_key);
CREATE INDEX ix_fait_paiement_date ON dwh.fait_paiement (date_paiement_key);