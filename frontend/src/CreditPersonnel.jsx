import { useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { appeler } from "./api";
import { useAuth } from "./auth.jsx";
import { dateFr, fcfa } from "./formats.js";
import Cadre from "./Cadre.jsx";
import {
  Alerte, Badge, Bouton, Champ, Chargement, Info, Infos, Panneau, TD, TH, Tableau, classeSaisie,
} from "./ui.jsx";

const MODES = { especes: "Espèces", mobile_money: "Mobile money", virement: "Virement" };

function joli(texte) {
  const t = String(texte).replace(/_/g, " ");
  return t.charAt(0).toUpperCase() + t.slice(1);
}

function tonStatut(statut, retard) {
  const s = String(statut).toLowerCase();
  if (retard > 0 || s.includes("retard")) return "rouge";
  if (s.includes("pay") || s.includes("sold")) return "vert";
  return "neutre";
}

export default function CreditPersonnel() {
  const { id } = useParams();
  const { utilisateur } = useAuth();
  const [situation, setSituation] = useState(null);
  const [paiements, setPaiements] = useState([]);
  const [erreur, setErreur] = useState("");
  const [succes, setSucces] = useState("");

  const [montant, setMontant] = useState("");
  const [datePaiement, setDatePaiement] = useState(new Date().toISOString().slice(0, 10));
  const [mode, setMode] = useState("especes");
  const [envoi, setEnvoi] = useState(false);

  const charger = useCallback(async () => {
    try {
      const [s, p] = await Promise.all([
        appeler("/credits/" + id + "/situation"),
        appeler("/credits/" + id + "/paiements"),
      ]);
      setSituation(s);
      setPaiements(Array.isArray(p) ? p : []);
    } catch (e) {
      setErreur(e.message);
    }
  }, [id]);

  useEffect(() => {
    charger();
  }, [charger]);

  async function enregistrer(e) {
    e.preventDefault();
    setErreur("");
    setSucces("");
    const valeur = Number(montant);
    if (!valeur || valeur <= 0) {
      setErreur("Saisissez un montant supérieur à zéro.");
      return;
    }
    setEnvoi(true);
    try {
      await appeler("/credits/" + id + "/paiements", {
        methode: "POST",
        json: { montant: valeur, date_paiement: datePaiement, mode },
      });
      setSucces("Paiement de " + fcfa(valeur) + " enregistré.");
      setMontant("");
      await charger();
    } catch (err) {
      setErreur(err.message);
    } finally {
      setEnvoi(false);
    }
  }

  if (!situation) {
    return (
      <Cadre titre={"Crédit n° " + id}>
        {erreur ? <Alerte>{erreur}</Alerte> : <Chargement />}
      </Cadre>
    );
  }

  const pourcentage = situation.total_du > 0 ? Math.round((100 * situation.total_paye) / situation.total_du) : 0;
  const prochaine = situation.echeances.find((x) => x.reste_du > 0);
  const peutSaisir = utilisateur.role !== "decideur";

  return (
    <Cadre titre={"Crédit n° " + id}
      actions={situation.solde
        ? <Badge ton="vert">Soldé</Badge>
        : situation.nb_echeances_en_retard > 0 ? <Badge ton="rouge">En retard</Badge> : null}>
      {erreur && <Alerte>{erreur}</Alerte>}
      {succes && <Alerte ton="succes">{succes}</Alerte>}

      <Panneau titre="Situation">
        <div className="mb-1 h-2.5 overflow-hidden rounded-full bg-slate-200">
          <div className="h-full bg-emerald-600" style={{ width: pourcentage + "%" }} />
        </div>
        <p className="mb-4 text-xs text-slate-500">{pourcentage} % du total déjà payé</p>
        <Infos>
          <Info libelle="Total à rembourser">{fcfa(situation.total_du)}</Info>
          <Info libelle="Déjà payé">{fcfa(situation.total_paye)}</Info>
          <Info libelle="Reste à payer">{fcfa(situation.reste_a_payer)}</Info>
          <Info libelle="Capital restant">{fcfa(situation.capital_restant)}</Info>
          <Info libelle="Échéances en retard">
            {situation.nb_echeances_en_retard} ({fcfa(situation.montant_en_retard)})
          </Info>
          <Info libelle="Retard le plus long">{situation.jours_retard_max} jour(s)</Info>
        </Infos>
      </Panneau>

      {peutSaisir && !situation.solde && (
        <Panneau titre="Enregistrer un paiement">
          <form onSubmit={enregistrer} className="grid gap-4 sm:grid-cols-3">
            <Champ label="Montant (FCFA)"
              aide={prochaine ? "Prochaine échéance à solder : " + fcfa(prochaine.reste_du) : undefined}>
              <input className={classeSaisie} type="number" inputMode="numeric" min="1" step="1" required
                value={montant} onChange={(e) => setMontant(e.target.value)} />
            </Champ>
            <Champ label="Date du paiement">
              <input className={classeSaisie} type="date" required value={datePaiement}
                onChange={(e) => setDatePaiement(e.target.value)} />
            </Champ>
            <Champ label="Mode de paiement">
              <select className={classeSaisie} value={mode} onChange={(e) => setMode(e.target.value)}>
                {Object.entries(MODES).map(([valeur, libelle]) => (
                  <option key={valeur} value={valeur}>{libelle}</option>
                ))}
              </select>
            </Champ>
            <div className="flex flex-wrap gap-2 sm:col-span-3">
              <Bouton type="submit" disabled={envoi}>{envoi ? "Enregistrement…" : "Enregistrer le paiement"}</Bouton>
              {prochaine && (
                <Bouton variante="secondaire" onClick={() => setMontant(String(prochaine.reste_du))}>
                  Remplir avec l'échéance n° {prochaine.numero}
                </Bouton>
              )}
            </div>
          </form>
          <p className="mt-3 text-xs text-slate-500">
            Un paiement est définitif : il ne peut ni être modifié ni supprimé (registre en ajout seul).
          </p>
        </Panneau>
      )}

      <Panneau titre="Échéances">
        <Tableau>
          <thead className="bg-slate-50">
            <tr>
              <th className={TH}>N°</th><th className={TH}>Date</th><th className={TH}>À payer</th>
              <th className={TH}>Payé</th><th className={TH}>Reste</th><th className={TH}>État</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {situation.echeances.map((e) => (
              <tr key={e.numero}>
                <td className={TD}>{e.numero}</td>
                <td className={TD}>{dateFr(e.date_echeance)}</td>
                <td className={TD}>{fcfa(e.montant_du)}</td>
                <td className={TD}>{fcfa(e.montant_paye)}</td>
                <td className={TD}>{fcfa(e.reste_du)}</td>
                <td className={TD}>
                  <Badge ton={tonStatut(e.statut, e.jours_retard)}>
                    {joli(e.statut)}{e.jours_retard > 0 ? " (" + e.jours_retard + " j)" : ""}
                  </Badge>
                </td>
              </tr>
            ))}
          </tbody>
        </Tableau>
      </Panneau>

      <Panneau titre="Historique des paiements">
        {paiements.length === 0 && <p className="text-sm text-slate-500">Aucun paiement enregistré.</p>}
        {paiements.length > 0 && (
          <Tableau>
            <thead className="bg-slate-50">
              <tr><th className={TH}>Date</th><th className={TH}>Montant</th><th className={TH}>Mode</th></tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {paiements.map((p, i) => (
                <tr key={p.id ?? i}>
                  <td className={TD}>{dateFr(p.date_paiement)}</td>
                  <td className={TD}>{fcfa(p.montant)}</td>
                  <td className={TD}>{MODES[p.mode] || p.mode}</td>
                </tr>
              ))}
            </tbody>
          </Tableau>
        )}
      </Panneau>
      <p><Link className="text-marque-700 underline" to="/dossiers">Retour aux dossiers</Link></p>
    </Cadre>
  );
}
