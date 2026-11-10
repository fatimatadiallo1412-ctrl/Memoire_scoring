import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { appeler } from "./api";
import { useAuth } from "./auth.jsx";
import { dateFr, fcfa } from "./formats.js";
import { LIBELLE_STATUT } from "./listes.js";
import Cadre from "./Cadre.jsx";
import { Alerte, Badge, TD, TH, Tableau, classeSaisie, tonDossier } from "./ui.jsx";

function nomClient(c) {
  return c.prenom + " " + c.nom + " (" + c.code_client + ")";
}

export default function Dossiers() {
  const { utilisateur } = useAuth();
  const [statut, setStatut] = useState(utilisateur.role === "decideur" ? "soumis_decision" : "");
  const [q, setQ] = useState("");
  const [demandes, setDemandes] = useState([]);
  const [noms, setNoms] = useState({});
  const [nbClients, setNbClients] = useState(null);
  const [erreur, setErreur] = useState("");
  const [chargement, setChargement] = useState(true);

  useEffect(() => {
    const terme = q.trim();
    if (terme.length === 1) return; // l'API exige au moins 2 caractères
    let annule = false;
    const minuteur = setTimeout(async () => {
      setChargement(true);
      setErreur("");
      try {
        if (!terme) {
          const liste = await appeler("/demandes", { params: { statut, limite: 50 } });
          if (!annule) {
            setNbClients(null);
            setDemandes(liste);
          }
        } else {
          const clients = await appeler("/clients", { params: { q: terme, limite: 20 } });
          const listes = await Promise.all(
            clients.map((c) => appeler("/demandes", { params: { client_id: c.id, statut, limite: 50 } }))
          );
          if (!annule) {
            setNoms((a) => ({ ...a, ...Object.fromEntries(clients.map((c) => [c.id, nomClient(c)])) }));
            setNbClients(clients.length);
            setDemandes(listes.flat().sort((x, y) => y.id - x.id));
          }
        }
      } catch (e) {
        if (!annule) setErreur(e.message);
      } finally {
        if (!annule) setChargement(false);
      }
    }, 300);
    return () => {
      annule = true;
      clearTimeout(minuteur);
    };
  }, [q, statut]);

  // Noms des clients de la liste (hors recherche)
  useEffect(() => {
    const manquants = [...new Set(demandes.map((d) => d.client_id))].filter((id) => !(id in noms));
    if (manquants.length === 0) return;
    Promise.all(
      manquants.map((id) =>
        appeler("/clients/" + id)
          .then((c) => [id, nomClient(c)])
          .catch(() => [id, "Client n° " + id])
      )
    ).then((paires) => setNoms((a) => ({ ...a, ...Object.fromEntries(paires) })));
  }, [demandes]); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <Cadre titre={utilisateur.role === "decideur" ? "Dossiers" : "Dossiers de crédit"}>
      <div className="mb-3 grid gap-3 sm:grid-cols-3">
        <input
          className={classeSaisie + " sm:col-span-2"}
          type="search"
          placeholder="Rechercher un client : nom, prénom, téléphone ou code (2 caractères minimum)"
          value={q}
          onChange={(e) => setQ(e.target.value)}
        />
        <select className={classeSaisie} value={statut} onChange={(e) => setStatut(e.target.value)}
          aria-label="Filtrer par statut">
          <option value="">Tous les statuts</option>
          {Object.entries(LIBELLE_STATUT).map(([cle, libelle]) => (
            <option key={cle} value={cle}>{libelle}</option>
          ))}
        </select>
      </div>
      {erreur && <Alerte>{erreur}</Alerte>}
      <p className="mb-3 text-sm text-slate-500">
        {chargement
          ? "Chargement…"
          : demandes.length + " dossier(s)" +
            (nbClients !== null ? " pour " + nbClients + " client(s) trouvé(s)" : "") + "." +
            (nbClients === 20 ? " Résultats limités : précisez la recherche." : "")}
      </p>
      <Tableau>
        <thead className="bg-slate-50">
          <tr>
            <th className={TH}>Numéro</th><th className={TH}>Client</th><th className={TH}>Montant</th>
            <th className={TH + " hidden md:table-cell"}>Durée</th>
            <th className={TH + " hidden md:table-cell"}>Date</th>
            <th className={TH}>Statut</th><th className={TH}></th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100 bg-white">
          {demandes.map((d) => (
            <tr key={d.id} className="hover:bg-slate-50">
              <td className={TD}>{d.numero}</td>
              <td className={TD}>{noms[d.client_id] || "…"}</td>
              <td className={TD + " whitespace-nowrap"}>{fcfa(d.montant_demande)}</td>
              <td className={TD + " hidden md:table-cell"}>{d.duree_mois} mois</td>
              <td className={TD + " hidden md:table-cell"}>{dateFr(d.date_demande)}</td>
              <td className={TD}><Badge ton={tonDossier(d.statut)}>{LIBELLE_STATUT[d.statut] || d.statut}</Badge></td>
              <td className={TD + " text-right"}>
                <Link className="text-marque-700 underline" to={"/dossiers/" + d.id}>Ouvrir</Link>
              </td>
            </tr>
          ))}
        </tbody>
      </Tableau>
    </Cadre>
  );
}
