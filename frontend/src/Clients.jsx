import { useEffect, useState } from "react";
import { appelerPage } from "./api";
import { useAuth } from "./useAuth.js";
import { dateFr } from "./formats.js";
import Cadre from "./Cadre.jsx";
import Pagination from "./Pagination.jsx";
import { bornesPage } from "./usePagination.js";

const PAR_PAGE = 10;
import { Alerte, LienBouton, TD, TH, Tableau, classeSaisie, LienOuvrir } from "./ui.jsx";

export default function Clients() {
  const { utilisateur } = useAuth();
  const peutCreer = utilisateur.role === "agent_credit";
  const [q, setQ] = useState("");
  const [clients, setClients] = useState([]);
  const [erreur, setErreur] = useState("");
  const [chargement, setChargement] = useState(true);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);

  useEffect(() => {
    const terme = q.trim();
    if (terme.length === 1) return; // l'API exige au moins 2 caractères
    let annule = false;
    const minuteur = setTimeout(async () => {
      setChargement(true);
      setErreur("");
      try {
        const { elements, total: nb } = await appelerPage("/clients", {
          params: { q: terme, limite: PAR_PAGE, decalage: (page - 1) * PAR_PAGE },
        });
        if (!annule) {
          setClients(elements);
          setTotal(nb);
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
  }, [q, page]);

  return (
    <Cadre titre="Clients" actions={peutCreer && <LienBouton to="/clients/nouveau">+ Nouveau client</LienBouton>}>
      <input
        className={classeSaisie + " mb-3"}
        type="search"
        placeholder="Nom, prénom, téléphone ou code client (2 caractères minimum)"
        value={q}
        onChange={(e) => { setQ(e.target.value); setPage(1); }}
      />
      {erreur && <Alerte>{erreur}</Alerte>}
      <p className="mb-3 text-sm text-slate-500">
        {chargement
          ? "Recherche…"
          : total + " client(s). Plusieurs clients peuvent porter le même nom : repérez le bon par la date de naissance, le téléphone ou le code client."}
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
        <tbody key={page} className="animate-apparition divide-y divide-slate-100 bg-white">
          {clients.map((c) => (
            <tr key={c.id} className="hover:bg-slate-50">
              <td className={TD}>{c.code_client}</td>
              <td className={TD + " font-medium"}>{c.nom}</td>
              <td className={TD}>{c.prenom}</td>
              <td className={TD + " hidden md:table-cell"}>{dateFr(c.date_naissance)}</td>
              <td className={TD}>{c.telephone}</td>
              <td className={TD + " hidden lg:table-cell"}>{c.adresse}</td>
              <td className={TD + " text-right"}>
                <LienOuvrir to={"/clients/" + c.id}>Ouvrir</LienOuvrir>
              </td>
            </tr>
          ))}
        </tbody>
      </Tableau>
      <Pagination {...bornesPage(page, total, PAR_PAGE, clients.length)} allerA={setPage} />
    </Cadre>
  );
}
