import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { appeler } from "./api";
import { dateFr, fcfa } from "./formats.js";
import Cadre from "./Cadre.jsx";
import RetourClient from "./RetourClient.jsx";
import { Alerte, Badge, Bouton, Chargement, LienOuvrir, Panneau, TD, TH, Tableau } from "./ui.jsx";

// Statut d'une demande, en mots simples pour le client.
const ETAT_DEMANDE = {
  accorde: ["Accordée", "vert"],
  accorde_modifie: ["Accordée, montant réduit", "orange"],
  refuse: ["Non acceptée", "rouge"],
  ajourne: ["Reportée", "orange"],
  decaisse: ["Accordée", "vert"],
  en_remboursement: ["Accordée", "vert"],
  solde: ["Remboursée", "vert"],
  contentieux: ["Accordée", "vert"],
};

function MesDemandes({ demandes }) {
  if (demandes.length === 0) return null;
  return (
    <Panneau titre="Mes demandes de crédit">
      <ul className="space-y-4">
        {demandes.map((d) => {
          const [libelle, ton] = ETAT_DEMANDE[d.statut] || ["En cours d'étude", "neutre"];
          return (
            <li key={d.id} className="rounded-carte border border-bord p-4">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <p className="text-sm">
                  <span className="font-semibold text-encre">{fcfa(d.montant_demande)} sur {d.duree_mois} mois</span>
                  <span className="text-texte-doux"> · {d.produit} · demandé le {dateFr(d.date_demande)}</span>
                </p>
                <Badge ton={ton}>{libelle}</Badge>
              </div>
              {d.retour && d.retour.montant_accorde && (
                <p className="mt-2 text-sm">Montant accordé : <strong>{fcfa(d.retour.montant_accorde)}</strong> sur {d.retour.duree_accordee} mois.</p>
              )}
              {d.retour && <div className="mt-4"><RetourClient retour={d.retour} /></div>}
            </li>
          );
        })}
      </ul>
    </Panneau>
  );
}

export default function Espace() {
  const [prochaine, setProchaine] = useState(undefined);
  const [rappels, setRappels] = useState([]);
  const [credits, setCredits] = useState([]);
  const [demandes, setDemandes] = useState([]);
  const [erreur, setErreur] = useState("");

  const charger = useCallback(async () => {
    try {
      const [p, r, c, d] = await Promise.all([
        appeler("/moi/prochaine-echeance"),
        appeler("/moi/rappels", { params: { limite: 10 } }),
        appeler("/moi/credits"),
        appeler("/moi/demandes"),
      ]);
      setProchaine(p);
      setRappels(r);
      setCredits(c);
      setDemandes(d);
    } catch (e) {
      setErreur(e.message);
    }
  }, []);

  useEffect(() => {
    // oxlint-disable-next-line react/set-state-in-effect -- chargement depuis l'API (système externe)
    charger();
  }, [charger]);

  async function marquerLu(id) {
    try {
      await appeler("/moi/rappels/" + id + "/lu", { methode: "POST" });
      window.dispatchEvent(new Event("rappels-maj"));
      await charger();
    } catch (e) {
      setErreur(e.message);
    }
  }

  return (
    <Cadre titre="Mon espace">
      {erreur && <Alerte>{erreur}</Alerte>}

      <Panneau titre="Prochaine échéance">
        {prochaine === undefined && <Chargement />}
        {prochaine === null && <p>Aucune échéance à payer. Merci !</p>}
        {prochaine && (
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <p>
                Échéance n° {prochaine.numero} du <strong>{dateFr(prochaine.date_echeance)}</strong>
              </p>
              <p className="mt-1 text-2xl font-semibold text-slate-900">{fcfa(prochaine.reste_du)}</p>
              <div className="mt-2">
                {prochaine.en_retard
                  ? <Badge ton="rouge">En retard de {Math.abs(prochaine.jours)} jour(s)</Badge>
                  : <Badge ton="vert">Dans {Math.abs(prochaine.jours)} jour(s)</Badge>}
              </div>
            </div>
            <Link to={"/espace/credits/" + prochaine.credit_id}
              className="inline-flex justify-center rounded-md bg-marque-700 px-4 py-2 text-sm font-medium text-white hover:bg-marque-800">
              Voir le détail du crédit
            </Link>
          </div>
        )}
      </Panneau>

      <Panneau titre="Mes rappels">
        {rappels.length === 0 && <p className="text-sm text-slate-500">Aucun rappel pour le moment.</p>}
        <div className="grid gap-2">
          {rappels.map((r) => (
            <div key={r.id}
              className={"rounded-md border-l-4 px-3 py-2 " +
                (r.lu_le ? "border-slate-300 bg-slate-50 text-slate-600" : "border-marque-600 bg-marque-50 font-medium text-slate-900")}>
              <p className="text-sm">{r.message}</p>
              <p className="mt-1 flex flex-wrap items-center gap-3 text-xs font-normal text-slate-500">
                {dateFr(r.jour)}
                {!r.lu_le && (
                  <Bouton variante="lien" className="text-xs" onClick={() => marquerLu(r.id)}>
                    Marquer comme lu
                  </Bouton>
                )}
              </p>
            </div>
          ))}
        </div>
      </Panneau>

      <MesDemandes demandes={demandes} />

      <Panneau titre="Mes crédits">
        {credits.length === 0 && <p className="text-sm text-slate-500">Vous n'avez pas de crédit.</p>}
        {credits.length > 0 && (
          <Tableau>
            <thead className="bg-slate-50">
              <tr>
                <th className={TH}>Décaissé le</th><th className={TH}>Montant</th>
                <th className={TH}>Durée</th><th className={TH}>Mensualité</th><th className={TH}></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {credits.map((c) => (
                <tr key={c.id}>
                  <td className={TD}>{dateFr(c.date_decaissement)}</td>
                  <td className={TD}>{fcfa(c.montant_accorde)}</td>
                  <td className={TD}>{c.duree_mois} mois</td>
                  <td className={TD}>{fcfa(c.mensualite)}</td>
                  <td className={TD + " text-right"}>
                    <LienOuvrir to={"/espace/credits/" + c.id}>Détails</LienOuvrir>
                  </td>
                </tr>
              ))}
            </tbody>
          </Tableau>
        )}
      </Panneau>
    </Cadre>
  );
}
