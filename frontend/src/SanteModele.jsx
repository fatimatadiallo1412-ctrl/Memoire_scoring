import { useCallback, useEffect, useState } from "react";
import { Activity, Gauge, RefreshCw, Scale, ShieldCheck, Users } from "lucide-react";
import { appeler } from "./api";
import Cadre from "./Cadre.jsx";
import { LIBELLE_DECISION } from "./listes.js";
import { Alerte, Badge, Bouton, Chargement, Info, Infos, Panneau, Statistique, TD, TH, Tableau } from "./ui.jsx";

const TON_NIVEAU = { vert: "vert", orange: "orange", rouge: "rouge" };
const LIBELLE_NIVEAU = { vert: "Stable", orange: "À surveiller", rouge: "Action requise", "n/a": "Non jugé" };

const INDICATEURS = {
  psi_score: ["Stabilité des scores", "Les scores de la période ressemblent-ils à ceux de la population de référence ?"],
  psi_variables: ["Stabilité des profils", "Variable dont la répartition a le plus changé (âge, profession, ratios…)."],
  modalites_inconnues: ["Valeurs inconnues du modèle", "Dossiers dont une catégorie (profession, logement…) n'existait pas à l'entraînement : le modèle l'ignore."],
  derogations: ["Dérogations", "Décisions du directeur contraires à la recommandation du modèle."],
  calibration: ["Calibration", "Défaut prévu par le modèle comparé au défaut réellement observé."],
  auc: ["Pouvoir de classement (AUC)", "Le modèle distingue-t-il toujours les bons et les mauvais payeurs ?"],
};

const LIBELLE_VARIABLE = {
  CNT_CHILDREN: "Nombre d'enfants", CNT_FAM_MEMBERS: "Taille du ménage", age_ans: "Âge",
  anciennete_emploi_ans: "Ancienneté dans l'activité", sans_emploi: "Sans activité déclarée",
  credit_sur_revenu: "Montant / revenu", annuite_sur_revenu: "Mensualité / revenu",
  duree_implicite: "Durée du crédit", NAME_INCOME_TYPE: "Type de revenu", NAME_FAMILY_STATUS: "Situation familiale",
  NAME_HOUSING_TYPE: "Logement", OCCUPATION_TYPE: "Profession", FLAG_OWN_REALTY: "Bien immobilier", FLAG_OWN_CAR: "Véhicule",
};

const LIBELLE_RECO = { accord: "accord", accord_reduit: "accord réduit", refus: "refus" };

const pct = (x, d = 1) => (x === null || x === undefined ? "–" : (100 * x).toFixed(d).replace(".", ",") + " %");
const nb = (x, d = 3) => (x === null || x === undefined ? "–" : Number(x).toFixed(d).replace(".", ","));
const jour = (iso) => new Date(iso).toLocaleDateString("fr-FR");
const dateHeure = (iso) => {
  const d = new Date(iso);
  return d.toLocaleDateString("fr-FR") + " à " + d.toLocaleTimeString("fr-FR", { hour: "2-digit", minute: "2-digit" });
};

function Niveau({ niveau }) {
  return <Badge ton={TON_NIVEAU[niveau] || "neutre"}>{LIBELLE_NIVEAU[niveau] || niveau}</Badge>;
}

function BandeauGlobal({ rapport, produitLe, automatique }) {
  const n = rapport.niveau_global;
  const ton = n === "rouge" ? "erreur" : n === "orange" ? "attention" : n === "vert" ? "succes" : "info";
  return (
    <Alerte ton={ton}>
      <span className="font-semibold">{LIBELLE_NIVEAU[n] || n}.</span> {rapport.action}
      <span className="mt-1 block text-xs opacity-80">
        Période du {jour(rapport.periode[0])} au {jour(rapport.periode[1])} · rapport {automatique ? "automatique" : "demandé"} le {dateHeure(produitLe)}
      </span>
    </Alerte>
  );
}

function Indicateurs({ rapport }) {
  return (
    <Panneau titre="Indicateurs">
      <ul className="divide-y divide-bord">
        {/* Ordre fixe : la base (JSONB) ne conserve pas l'ordre des clés */}
        {Object.keys(INDICATEURS).filter((cle) => cle in rapport.alertes).map((cle) => {
          const niveau = rapport.alertes[cle];
          const [titre, aide] = INDICATEURS[cle] || [cle, ""];
          return (
            <li key={cle} className="flex flex-wrap items-start justify-between gap-3 py-3">
              <div className="min-w-0 flex-1">
                <p className="font-medium text-encre">{titre}</p>
                <p className="text-sm text-texte-doux">{aide}</p>
              </div>
              <Niveau niveau={niveau} />
            </li>
          );
        })}
      </ul>
    </Panneau>
  );
}

function Stabilite({ rapport, seuils }) {
  if (!rapport.psi) {
    return <Panneau titre="Stabilité"><p className="text-sm text-texte-doux">Pas de population de référence : {rapport.reference}</p></Panneau>;
  }
  const { variables, exces } = rapport.psi;
  const lignes = Object.keys(variables).sort((a, b) => exces[b] - exces[a] || variables[b] - variables[a]);
  const inconnues = rapport.modalites_inconnues;
  return (
    <Panneau titre="Stabilité de la population">
      <p className="mb-4 text-sm text-texte-doux">
        Référence : {rapport.reference}. L'indice PSI mesure l'écart de répartition. Seul l'excès au-delà du simple hasard
        déclenche une alerte (à surveiller dès {nb(seuils.psi[0], 2)}, action dès {nb(seuils.psi[1], 2)}).
      </p>
      <Tableau>
        <thead><tr><th className={TH}>Variable</th><th className={TH}>PSI</th><th className={TH}>Excès sur le hasard</th></tr></thead>
        <tbody>
          <tr className="font-semibold"><td className={TD}>Score du modèle</td><td className={TD}>{nb(rapport.psi.score)}</td><td className={TD}>{nb(exces.score)}</td></tr>
          {lignes.map((v) => (
            <tr key={v}>
              <td className={TD}>{LIBELLE_VARIABLE[v] || v}</td>
              <td className={TD}>{nb(variables[v])}</td>
              <td className={TD}>
                <span className={exces[v] >= seuils.psi[1] ? "font-semibold text-risque-eleve" : exces[v] >= seuils.psi[0] ? "font-semibold text-risque-moyen" : ""}>{nb(exces[v])}</span>
              </td>
            </tr>
          ))}
        </tbody>
      </Tableau>
      {inconnues && (
        <p className="mt-4 text-sm">
          Dossiers avec une valeur inconnue du modèle : <strong>{pct(inconnues.part_dossiers)}</strong>
          {Object.entries(inconnues.exemples).map(([v, ex]) => (
            <span key={v} className="block text-texte-doux">{LIBELLE_VARIABLE[v] || v} : {Object.keys(ex).join(", ")}</span>
          ))}
        </p>
      )}
    </Panneau>
  );
}

function Performance({ perf, seuils }) {
  return (
    <Panneau titre="Performance sur les crédits arrivés à maturité">
      <p className="mb-4 text-sm text-texte-doux">
        Crédits dont la période d'observation (durée, au plus 12 mois, plus 90 jours) s'est terminée dans les 12 derniers mois.
        Un défaut est un retard de plus de 90 jours. En dessous de {seuils.min_defauts} défauts, la performance n'est pas jugée.
      </p>
      {perf.n === 0 ? <p className="text-sm">Aucun crédit arrivé à maturité.</p> : (
        <>
          <Infos>
            <Info libelle="Crédits observés">{perf.n}</Info>
            <Info libelle="Défauts">{perf.n_defauts}</Info>
            <Info libelle="Défaut prévu / observé">{pct(perf.taux_prevu)} / {pct(perf.taux_observe)}</Info>
            <Info libelle="AUC">{perf.auc !== undefined ? nb(perf.auc) : "non jugée"}</Info>
            <Info libelle="Score de Brier">{nb(perf.brier, 4)}</Info>
          </Infos>
          {perf.verdict && <p className="mt-4 text-sm text-texte-doux">{perf.verdict}.</p>}
          <div className="mt-4">
            <Tableau>
              <thead><tr><th className={TH}>Classe de risque</th><th className={TH}>Crédits</th><th className={TH}>Défaut prévu</th><th className={TH}>Défaut observé</th></tr></thead>
              <tbody>
                {perf.calibration.map((c) => (
                  <tr key={c.classe}>
                    <td className={TD}>{c.classe + 1} {c.classe === 0 ? "(moins risqués)" : c.classe === perf.calibration.length - 1 ? "(plus risqués)" : ""}</td>
                    <td className={TD}>{c.n}</td><td className={TD}>{pct(c.prevu)}</td><td className={TD}>{pct(c.observe)}</td>
                  </tr>
                ))}
              </tbody>
            </Tableau>
          </div>
        </>
      )}
    </Panneau>
  );
}

export default function SanteModele() {
  const [etat, setEtat] = useState(null);
  const [erreur, setErreur] = useState("");
  const [calcul, setCalcul] = useState(false);

  const charger = useCallback(async () => {
    setErreur("");
    try { setEtat(await appeler("/modele/sante")); } catch (e) { setErreur(e.message); }
  }, []);

  useEffect(() => {
    // oxlint-disable-next-line react/set-state-in-effect -- chargement depuis l'API (système externe)
    charger();
  }, [charger]);

  async function produire() {
    setErreur("");
    setCalcul(true);
    try { setEtat(await appeler("/modele/sante", { methode: "POST" })); } catch (e) { setErreur(e.message); }
    setCalcul(false);
  }

  const r = etat?.dernier?.contenu;
  const fiche = etat?.fiche;
  const d = r?.decisions;
  return (
    <Cadre titre="Santé du modèle">
      {erreur && <Alerte>{erreur}</Alerte>}
      {!etat && !erreur && <Chargement />}
      {etat && (
        <>
          <div className="mb-5 flex flex-wrap items-center justify-between gap-3">
            <p className="text-sm text-texte-doux">
              Modèle en service : <strong className="text-encre">{etat.version_en_service}</strong>. Un rapport est produit
              automatiquement le 1er de chaque mois, sur les trois derniers mois.
            </p>
            <Bouton className="gap-1.5" onClick={produire} disabled={calcul}>
              <RefreshCw className={"h-4 w-4" + (calcul ? " animate-spin" : "")} aria-hidden="true" />
              {calcul ? "Calcul en cours…" : "Produire un rapport maintenant"}
            </Bouton>
          </div>

          {!r && <Alerte ton="info">Aucun rapport pour l'instant. Utilisez le bouton ci-dessus pour produire le premier.</Alerte>}
          {r && (
            <>
              <BandeauGlobal rapport={r} produitLe={etat.dernier.produit_le} automatique={etat.dernier.automatique} />
              <div className="mb-6 mt-6 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
                <Statistique icone={Users} valeur={r.dossiers_scores} libelle="Dossiers scorés" />
                <Statistique icone={Gauge} valeur={pct(r.score_moyen)} libelle="Risque moyen prévu" ton="bg-soleil-50 text-soleil-fonce" />
                <Statistique icone={ShieldCheck} valeur={d?.n ? pct(d.taux_acceptation, 0) : "–"} libelle="Taux d'acceptation" ton="bg-baobab-50 text-baobab" />
                <Statistique icone={Scale} valeur={d?.n ? pct(d.taux_derogation) : "–"} libelle="Dérogations au modèle" ton="bg-risque-moyen-fond text-risque-moyen" />
              </div>
              <Indicateurs rapport={r} />
              <Stabilite rapport={r} seuils={etat.seuils} />
              {d?.n > 0 && Object.keys(d.derogations_par_sens).length > 0 && (
                <Panneau titre="Sens des dérogations">
                  <ul className="text-sm">
                    {Object.entries(d.derogations_par_sens).map(([sens, n]) => {
                      const [reco, decision] = sens.split(" -> ");
                      return <li key={sens} className="py-1">Recommandation « {LIBELLE_RECO[reco] || reco} », décision « {LIBELLE_DECISION[decision] || decision} » : <strong>{n}</strong></li>;
                    })}
                  </ul>
                </Panneau>
              )}
              <Performance perf={r.performance} seuils={etat.seuils} />
            </>
          )}

          {fiche && (
            <Panneau titre="Fiche du modèle en service">
              <Infos>
                <Info libelle="Type">{fiche.type || "–"}</Info>
                <Info libelle="Données d'apprentissage">{fiche.donnees || "–"}</Info>
                <Info libelle="AUC de référence">{nb(fiche.performances?.AUC)}</Info>
                <Info libelle="Mis en service le">{fiche.cree_le ? jour(fiche.cree_le) : "–"}</Info>
                <Info libelle="Validation">{fiche.validation || "–"}</Info>
              </Infos>
            </Panneau>
          )}

          {etat.historique.length > 0 && (
            <Panneau titre="Historique des rapports">
              <Tableau>
                <thead><tr><th className={TH}>Produit le</th><th className={TH}>Période</th><th className={TH}>Modèle</th><th className={TH}>Niveau</th></tr></thead>
                <tbody>
                  {etat.historique.map((h) => (
                    <tr key={h.id}>
                      <td className={TD}>{dateHeure(h.produit_le)}</td>
                      <td className={TD}>{jour(h.debut)} – {jour(h.fin)}</td>
                      <td className={TD}>{h.version_modele}</td>
                      <td className={TD}><Niveau niveau={h.niveau_global} /></td>
                    </tr>
                  ))}
                </tbody>
              </Tableau>
            </Panneau>
          )}
          <p className="flex items-center gap-1.5 text-xs text-texte-doux">
            <Activity className="h-3.5 w-3.5" aria-hidden="true" />
            Les seuils d'alerte sont des valeurs d'usage courant, à valider par la direction des risques.
          </p>
        </>
      )}
    </Cadre>
  );
}
