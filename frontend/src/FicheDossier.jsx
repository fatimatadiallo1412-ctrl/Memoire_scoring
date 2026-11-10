import { useCallback, useEffect, useRef, useState } from "react";
import { Check } from "lucide-react";
import { Link, useParams } from "react-router-dom";
import { appeler } from "./api";
import { useAuth } from "./auth.jsx";
import { dateFr, fcfa } from "./formats.js";
import { LIBELLE_DECISION, LIBELLE_STATUT } from "./listes.js";
import Cadre from "./Cadre.jsx";
import { EncadreDecaissement, PanneauDecaissement } from "./Decaissement.jsx";
import {
  Alerte, Badge, Bouton, Champ, Chargement, Info, Infos, LienBouton, Panneau,
  TD, TH, Tableau, classeSaisie, tonDossier,
} from "./ui.jsx";

const RECOMMANDATION = { accord: "Accord", accord_reduit: "Accord réduit", refus: "Refus" };
const STATUTS_CREDIT = ["decaisse", "en_remboursement", "solde", "contentieux"];

function pct(x) {
  return (Number(x) * 100).toFixed(1).replace(".", ",") + " %";
}

// Niveau de risque : celui de la recommandation du modèle (couleur + forme + texte).
const TON_RECOMMANDATION = { accord: "vert", accord_reduit: "orange", refus: "rouge" };
const COULEUR_JAUGE = { vert: "bg-risque-faible", orange: "bg-risque-moyen", rouge: "bg-risque-eleve" };

function JaugeScore({ p, seuil, ton }) {
  const [rempli, setRempli] = useState(false);
  useEffect(() => {
    const image = requestAnimationFrame(() => setRempli(true));
    return () => cancelAnimationFrame(image);
  }, []);
  const maximum = Math.min(1, Math.max(0.5, seuil * 1.6, p * 1.15));
  const largeur = Math.min(100, (p / maximum) * 100);
  const positionSeuil = Math.min(96, Math.max(4, (seuil / maximum) * 100));
  return (
    <div>
      <div
        role="meter" aria-label="Probabilité de défaut" aria-valuemin={0} aria-valuemax={100}
        aria-valuenow={Math.round(p * 1000) / 10}
        className="relative h-4 rounded-full bg-slate-200"
      >
        <div
          className={"h-full rounded-full transition-[width] duration-700 ease-out " + COULEUR_JAUGE[ton]}
          style={{ width: rempli ? largeur + "%" : "0%" }}
        />
        <div className="absolute -bottom-1.5 -top-1.5 w-0.5 bg-texte" style={{ left: positionSeuil + "%" }} />
      </div>
      <div className="relative mt-2 h-5 text-xs text-texte-doux">
        <span className="absolute left-0">0 %</span>
        <span className="absolute -translate-x-1/2 whitespace-nowrap font-medium text-texte" style={{ left: positionSeuil + "%" }}>
          Seuil appliqué : {pct(seuil)}
        </span>
      </div>
    </div>
  );
}

// Avancement du dossier sur son parcours normal (pas affiché pour refusé, ajourné, contentieux).
const PARCOURS = ["brouillon", "complet", "score", "instruit", "soumis_decision", "accorde", "decaisse", "en_remboursement"];
const RANG_SPECIAL = { accorde_modifie: 5, solde: 7 };

function ParcoursDossier({ statut }) {
  const courantRef = useRef(null);
  useEffect(() => {
    // Sur petit écran, l'étape en cours est amenée au centre du parcours.
    if (courantRef.current) courantRef.current.scrollIntoView({ inline: "center", block: "nearest" });
  }, [statut]);
  const rang = statut in RANG_SPECIAL ? RANG_SPECIAL[statut] : PARCOURS.indexOf(statut);
  if (rang < 0) return null;
  const termine = statut === "solde";
  return (
    <nav aria-label="Avancement du dossier" className="mb-5 overflow-x-auto rounded-carte border border-bord bg-white p-4 animate-apparition">
      <ol className="flex min-w-[40rem] items-start">
        {PARCOURS.map((etape, i) => {
          const fait = termine ? i <= rang : i < rang;
          const courant = !termine && i === rang;
          return (
            <li key={etape} ref={courant ? courantRef : undefined}
              className="relative flex flex-1 flex-col items-center text-center"
              aria-current={courant ? "step" : undefined}>
              {i > 0 && (
                <span aria-hidden="true"
                  className={"absolute left-[-50%] top-4 h-0.5 w-full " + (i <= rang ? "bg-marque-700" : "bg-slate-200")} />
              )}
              <span className={"relative z-10 flex h-8 w-8 items-center justify-center rounded-full text-sm font-semibold " +
                (fait ? "bg-marque-700 text-white"
                  : courant ? "bg-white text-marque-700 ring-2 ring-marque-700"
                    : "bg-slate-100 text-texte-doux")}>
                {fait ? <Check className="h-4 w-4" aria-hidden="true" /> : i + 1}
              </span>
              <span className={"mt-2 px-1 text-xs " + (courant ? "font-semibold text-marque-700" : "text-texte-doux")}>
                {LIBELLE_STATUT[etape]}
              </span>
            </li>
          );
        })}
      </ol>
    </nav>
  );
}

function ValeurFacteur({ valeur }) {
  if (valeur === null || valeur === undefined) return "—";
  if (Array.isArray(valeur)) {
    if (valeur.length === 0) return "—";
    return (
      <ul className="list-disc space-y-0.5 pl-5">
        {valeur.map((x, k) => <li key={k}>{typeof x === "object" ? JSON.stringify(x) : String(x)}</li>)}
      </ul>
    );
  }
  if (typeof valeur === "object") {
    return (
      <span className="flex flex-wrap gap-1.5">
        {Object.entries(valeur).map(([k, v]) => (
          <span key={k} className="inline-flex rounded bg-slate-100 px-2 py-0.5 text-xs">
            <span className="text-texte-doux">{k}</span>
            <span className="mx-1 text-texte-doux">:</span>
            <span className="font-medium">{typeof v === "object" ? JSON.stringify(v) : String(v)}</span>
          </span>
        ))}
      </span>
    );
  }
  return String(valeur);
}

function Facteurs({ facteurs }) {
  if (!facteurs) return null;
  const lignes = Array.isArray(facteurs) ? facteurs.map((x, i) => [String(i + 1), x]) : Object.entries(facteurs);
  return (
    <dl className="mt-2 divide-y divide-slate-100 rounded-champ border border-bord text-sm">
      {lignes.map(([cle, valeur]) => (
        <div key={cle} className="grid gap-1 px-3 py-2.5 sm:grid-cols-[minmax(10rem,14rem)_1fr] sm:gap-4">
          <dt className="font-medium text-slate-700">{cle}</dt>
          <dd className="text-texte"><ValeurFacteur valeur={valeur} /></dd>
        </div>
      ))}
    </dl>
  );
}

export default function FicheDossier() {
  const { id } = useParams();
  const { utilisateur } = useAuth();
  const gestion = utilisateur.role === "agent_credit";
  const directeur = utilisateur.role === "decideur";

  const [d, setD] = useState(null);
  const [client, setClient] = useState(null);
  const [score, setScore] = useState(null);
  const [decisions, setDecisions] = useState([]);
  const [credit, setCredit] = useState(null);
  const [ouvrirDec, setOuvrirDec] = useState(false);
  const [erreur, setErreur] = useState("");
  const [message, setMessage] = useState("");
  const [occupe, setOccupe] = useState(false);
  const [avis, setAvis] = useState("");
  const [dec, setDec] = useState({ decision: "accorder", montant: "", duree: "", commentaire: "" });

  const charger = useCallback(async () => {
    try {
      const demande = await appeler("/demandes/" + id);
      setD(demande);
      appeler("/clients/" + demande.client_id).then(setClient).catch(() => setClient(null));
      appeler("/demandes/" + id + "/score").then(setScore).catch(() => setScore(null));
      appeler("/demandes/" + id + "/decisions").then(setDecisions).catch(() => setDecisions([]));
      appeler("/demandes/" + id + "/credit").then(setCredit).catch(() => setCredit(null));
    } catch (e) {
      setErreur(e.message);
    }
  }, [id]);

  useEffect(() => {
    charger();
  }, [charger]);

  async function agir(chemin, json, succes) {
    setOccupe(true);
    setErreur("");
    setMessage("");
    try {
      await appeler("/demandes/" + id + chemin, { methode: "POST", json });
      setMessage(succes);
      await charger();
    } catch (e) {
      setErreur(e.message);
    } finally {
      setOccupe(false);
    }
  }

  function choisirDecision(valeur) {
    setDec((a) => ({
      ...a,
      decision: valeur,
      montant: a.montant || String((score && score.montant_suggere) || d.montant_demande),
      duree: a.duree || String(d.duree_mois),
    }));
  }

  function envoyerDecision(evenement) {
    evenement.preventDefault();
    const corps = { decision: dec.decision, commentaire: dec.commentaire.trim() || null };
    if (dec.decision === "accorder_modifie") {
      corps.montant_accorde = parseInt(dec.montant, 10);
      corps.duree_accordee = parseInt(dec.duree, 10);
    }
    agir("/decider", corps, "Décision enregistrée.");
  }

  if (!d) {
    return (
      <Cadre titre="Dossier">
        {erreur ? <Alerte>{erreur}</Alerte> : <Chargement />}
        <Link className="text-marque-700 underline" to="/dossiers">Retour aux dossiers</Link>
      </Cadre>
    );
  }

  return (
    <Cadre titre={"Dossier " + d.numero}
      actions={<Badge ton={tonDossier(d.statut)}>{LIBELLE_STATUT[d.statut] || d.statut}</Badge>}>
      {message && <Alerte ton="succes">{message}</Alerte>}
      {erreur && <Alerte>{erreur}</Alerte>}

      <ParcoursDossier statut={d.statut} />

      <Panneau titre="Demande">
        <Infos>
          <Info libelle="Client">
            <Link className="text-marque-700 underline" to={"/clients/" + d.client_id}>
              {client ? client.prenom + " " + client.nom : "Client n° " + d.client_id}
            </Link>
          </Info>
          <Info libelle="Montant demandé">{fcfa(d.montant_demande)}</Info>
          <Info libelle="Durée">{d.duree_mois} mois</Info>
          <Info libelle="Objet">{d.objet || "—"}</Info>
          <Info libelle="Date de la demande">{dateFr(d.date_demande)}</Info>
        </Infos>
        {d.avis_instruction && (
          <div className="mt-4">
            <h3 className="text-sm font-semibold text-slate-700">Avis d'instruction</h3>
            <p className="mt-1 text-sm">{d.avis_instruction}</p>
          </div>
        )}
      </Panneau>

      {score && (
        <Panneau titre="Score du modèle">
          {score.valide === false && (
            <Alerte ton="attention">
              Ce score n'est plus valide : les données du client ont changé depuis le calcul. Il faut le recalculer.
            </Alerte>
          )}
          <div className="grid gap-6 md:grid-cols-[auto_1fr] md:items-center md:gap-10">
            <div>
              <p className="text-xs uppercase tracking-wide text-texte-doux">Probabilité de défaut</p>
              <p className="mt-1 text-[clamp(2.25rem,1.5rem+3vw,3.25rem)] font-bold leading-none tabular-nums text-texte">
                {pct(score.p_defaut)}
              </p>
              <p className="mt-4 text-xs uppercase tracking-wide text-texte-doux">Recommandation</p>
              <div className="mt-1">
                <Badge ton={TON_RECOMMANDATION[score.recommandation] || "neutre"}>
                  {RECOMMANDATION[score.recommandation] || score.recommandation}
                </Badge>
              </div>
            </div>
            <JaugeScore key={score.p_defaut} p={Number(score.p_defaut)} seuil={Number(score.seuil_applique)}
              ton={TON_RECOMMANDATION[score.recommandation] || "vert"} />
          </div>
          <div className="mt-6 border-t border-slate-100 pt-4">
            <Infos>
              <Info libelle="Montant suggéré">{score.montant_suggere ? fcfa(score.montant_suggere) : "—"}</Info>
              <Info libelle="Modèle">{score.version_modele}</Info>
            </Infos>
          </div>
          {score.facteurs && (
            <div className="mt-5">
              <h3 className="text-sm font-semibold text-slate-700">Facteurs</h3>
              <Facteurs facteurs={score.facteurs} />
            </div>
          )}
        </Panneau>
      )}

      {gestion && (
        <Panneau titre="Actions">
          {d.statut === "brouillon" && (
            <Bouton disabled={occupe} onClick={() => agir("/completer", undefined, "Dossier marqué complet.")}>
              Marquer le dossier complet
            </Bouton>
          )}
          {(d.statut === "complet" || d.statut === "score") && (
            <Bouton disabled={occupe} onClick={() => agir("/scorer", undefined, "Score calculé.")}>
              {d.statut === "complet" ? "Calculer le score" : "Recalculer le score"}
            </Bouton>
          )}
          {d.statut === "score" && (
            <form className="mt-4 grid gap-3"
              onSubmit={(e) => { e.preventDefault(); agir("/instruire", { avis: avis.trim() }, "Avis enregistré."); }}>
              <Champ label="Avis d'instruction (10 caractères minimum)">
                <textarea className={classeSaisie} rows={4} value={avis} required minLength={10} maxLength={2000}
                  onChange={(e) => setAvis(e.target.value)} />
              </Champ>
              <div><Bouton type="submit" disabled={occupe}>Enregistrer l'avis</Bouton></div>
            </form>
          )}
          {d.statut === "instruit" && (
            <Bouton disabled={occupe} onClick={() => agir("/soumettre", undefined, "Dossier soumis à la décision.")}>
              Soumettre à la décision du directeur
            </Bouton>
          )}
          {["accorde", "accorde_modifie"].includes(d.statut) && (
            <Bouton disabled={occupe} onClick={() => setOuvrirDec(true)}>
              Décaisser le crédit
            </Bouton>
          )}
          {["refuse", "ajourne", "solde", "decaisse", "en_remboursement", "contentieux", "soumis_decision"].includes(d.statut) && (
            <p className="text-sm text-slate-500">Aucune action disponible pour ce statut.</p>
          )}
        </Panneau>
      )}

      {directeur && d.statut === "soumis_decision" && (
        <Panneau titre="Décision">
          <p className="mb-3 text-sm text-slate-500">
            Si votre décision diffère de la recommandation du modèle, un commentaire est obligatoire.
          </p>
          <form className="grid gap-4 sm:grid-cols-2" onSubmit={envoyerDecision}>
            <div className="sm:col-span-2">
              <Champ label="Décision">
                <select className={classeSaisie} value={dec.decision} onChange={(e) => choisirDecision(e.target.value)}>
                  {Object.entries(LIBELLE_DECISION).map(([cle, libelle]) => (
                    <option key={cle} value={cle}>{libelle}</option>
                  ))}
                </select>
              </Champ>
            </div>
            {dec.decision === "accorder_modifie" && (
              <>
                <Champ label="Montant accordé (FCFA)">
                  <input className={classeSaisie} type="number" min="1" value={dec.montant} required
                    onChange={(e) => setDec({ ...dec, montant: e.target.value })} />
                </Champ>
                <Champ label="Durée accordée (mois)">
                  <input className={classeSaisie} type="number" min="1" max="120" value={dec.duree} required
                    onChange={(e) => setDec({ ...dec, duree: e.target.value })} />
                </Champ>
              </>
            )}
            <div className="sm:col-span-2">
              <Champ label="Commentaire">
                <textarea className={classeSaisie} rows={3} value={dec.commentaire} maxLength={2000}
                  onChange={(e) => setDec({ ...dec, commentaire: e.target.value })} />
              </Champ>
            </div>
            <div className="sm:col-span-2">
              <Bouton type="submit" disabled={occupe}>Enregistrer la décision</Bouton>
            </div>
          </form>
        </Panneau>
      )}

      {decisions.length > 0 && (
        <Panneau titre="Historique des décisions">
          <Tableau>
            <thead className="bg-slate-50">
              <tr>
                <th className={TH}>Date</th><th className={TH}>Décision</th><th className={TH}>Montant</th>
                <th className={TH}>Durée</th><th className={TH}>Modèle</th><th className={TH}>Concordance</th>
                <th className={TH}>Commentaire</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {decisions.map((x) => (
                <tr key={x.id}>
                  <td className={TD + " whitespace-nowrap"}>{dateFr(x.decide_le.slice(0, 10))}</td>
                  <td className={TD}>{LIBELLE_DECISION[x.decision] || x.decision}</td>
                  <td className={TD + " whitespace-nowrap"}>{x.montant_accorde ? fcfa(x.montant_accorde) : "—"}</td>
                  <td className={TD + " whitespace-nowrap"}>{x.duree_accordee ? x.duree_accordee + " mois" : "—"}</td>
                  <td className={TD}>{RECOMMANDATION[x.recommandation_modele] || x.recommandation_modele || "—"}</td>
                  <td className={TD}>{x.concordance === null ? "—" : x.concordance ? "Oui" : "Non"}</td>
                  <td className={TD}>{x.commentaire || ""}</td>
                </tr>
              ))}
            </tbody>
          </Tableau>
        </Panneau>
      )}

      {credit && STATUTS_CREDIT.includes(d.statut) && (
        <Panneau titre="Crédit" droite={<LienBouton to={"/credits/" + credit.id}>Échéances et paiements</LienBouton>}>
          <Infos>
            <Info libelle="Montant accordé">{fcfa(credit.montant_accorde)}</Info>
            <Info libelle="Durée">{credit.duree_mois} mois</Info>
            <Info libelle="Taux annuel">{(Number(credit.taux_annuel) * 100).toFixed(1).replace(".", ",")} %</Info>
            <Info libelle="Mensualité">{fcfa(credit.mensualite)}</Info>
            <Info libelle="Décaissé le">{dateFr(credit.date_decaissement)}</Info>
          </Infos>
        </Panneau>
      )}

      {ouvrirDec && (
        <PanneauDecaissement demandeId={id} client={client} onFermer={() => setOuvrirDec(false)}
          onFini={() => { setOuvrirDec(false); setMessage("Crédit décaissé."); charger(); }} />
      )}
      {credit && <EncadreDecaissement credit={credit} client={client} />}

      <p><Link className="text-marque-700 underline" to="/dossiers">Retour aux dossiers</Link></p>
    </Cadre>
  );
}
