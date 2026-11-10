import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { appeler } from "./api";
import { useAuth } from "./auth.jsx";
import { dateFr } from "./formats.js";
import Cadre from "./Cadre.jsx";
import { Alerte, LienBouton, TD, TH, Tableau, classeSaisie } from "./ui.jsx";

export default function Clients() {
  const { utilisateur } = useAuth();
  const peutCreer = utilisateur.role === "agent_credit";
  const [q, setQ] = useState("");
  const [clients, setClients] = useState([]);
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
        const liste = await appeler("/clients", { params: { q: terme, limite: 50 } });
        if (!annule) setClients(liste);
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
  }, [q]);

  return (
    <Cadre titre="Clients" actions={peutCreer && <LienBouton to="/clients/nouveau">+ Nouveau client</LienBouton>}>
      <input
        className={classeSaisie + " mb-3"}
        type="search"
        placeholder="Nom, prénom, téléphone ou code client (2 caractères minimum)"
        value={q}
        onChange={(e) => setQ(e.target.value)}
      />
      {erreur && <Alerte>{erreur}</Alerte>}
      <p className="mb-3 text-sm text-slate-500">
        {chargement
          ? "Recherche…"
          : clients.length + " client(s). Plusieurs clients peuvent porter le même nom : repérez le bon par la date de naissance, le téléphone ou le code client."}
      </p>
      <Tableau>
        <thead className="bg-slate-50">
          <tr>
            <th className={TH}>Code</th><th className={TH}>Nom</th><th className={TH}>Prénom</th>
            <th className={TH + " hidden md:table-cell"}>Naissance</th>
            <th className={TH}>Téléphone</th>
            <th className={TH + " hidden lg:table-cell"}>Adresse</th>
            <th className={TH}></th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100 bg-white">
          {clients.map((c) => (
            <tr key={c.id} className="hover:bg-slate-50">
              <td className={TD}>{c.code_client}</td>
              <td className={TD + " font-medium"}>{c.nom}</td>
              <td className={TD}>{c.prenom}</td>
              <td className={TD + " hidden md:table-cell"}>{dateFr(c.date_naissance)}</td>
              <td className={TD}>{c.telephone}</td>
              <td className={TD + " hidden lg:table-cell"}>{c.adresse}</td>
              <td className={TD + " text-right"}>
                <Link className="text-marque-700 underline" to={"/clients/" + c.id}>Ouvrir</Link>
              </td>
            </tr>
          ))}
        </tbody>
      </Tableau>
    </Cadre>
  );
}
