import { useCallback, useEffect, useState } from "react";
import { CheckCheck, Inbox } from "lucide-react";
import { appeler } from "./api";
import Cadre from "./Cadre.jsx";
import Pagination from "./Pagination.jsx";
import { usePagination } from "./usePagination.js";
import { Alerte, Avatar, Badge, Bouton, Chargement } from "./ui.jsx";

function dateHeure(iso) {
  const d = new Date(iso);
  return d.toLocaleDateString("fr-FR") + " à " + d.toLocaleTimeString("fr-FR", { hour: "2-digit", minute: "2-digit" });
}

export default function Messages() {
  const [filtre, setFiltre] = useState("non_traites");
  const [liste, setListe] = useState(null);
  const pageMessages = usePagination(liste, 5);
  const [erreur, setErreur] = useState("");

  const charger = useCallback(async () => {
    setErreur("");
    try {
      const params = { limite: 100 };
      if (filtre === "non_traites") params.traite = "false";
      setListe(await appeler("/contact/messages", { params }));
    } catch (e) {
      setErreur(e.message);
    }
  }, [filtre]);

  useEffect(() => {
    setListe(null);
    charger();
  }, [charger]);

  async function traiter(id) {
    try {
      await appeler("/contact/messages/" + id + "/traite", { methode: "POST" });
      await charger();
    } catch (e) {
      setErreur(e.message);
    }
  }

  return (
    <Cadre titre="Messages reçus">
      <div className="mb-5 inline-flex rounded-full bg-white p-1 ring-1 ring-inset ring-bord" role="group" aria-label="Filtrer les messages">
        {[["non_traites", "Non traités"], ["tous", "Tous les messages"]].map(([valeur, libelle]) => (
          <button key={valeur} type="button" aria-pressed={filtre === valeur} onClick={() => setFiltre(valeur)}
            className={"min-h-10 rounded-full px-4 text-sm font-semibold transition duration-200 " +
              (filtre === valeur ? "bg-marque-700 text-white shadow-md" : "bg-transparent text-texte-doux hover:text-encre")}>
            {libelle}
          </button>
        ))}
      </div>
      {erreur && <Alerte>{erreur}</Alerte>}
      {!liste && !erreur && <Chargement />}
      {liste && liste.length === 0 && (
        <div className="flex animate-apparition flex-col items-center rounded-carte border border-dashed border-bord bg-white px-6 py-12 text-center">
          <span className="flex h-14 w-14 items-center justify-center rounded-2xl bg-marque-50 text-marque-700">
            <Inbox className="h-7 w-7" aria-hidden="true" />
          </span>
          <p className="mt-3 text-sm text-slate-500">Aucun message.</p>
        </div>
      )}
      <div key={pageMessages.page} className="grid animate-apparition gap-4">
      {liste && pageMessages.elements.map((m) => (
        <article key={m.id}
          className={"rounded-carte border bg-white p-5 transition duration-300 hover:shadow-md sm:p-6 " +
            (m.traite ? "border-bord" : "border-bord border-l-4 border-l-soleil")}>
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div className="flex min-w-0 items-center gap-3">
              <Avatar nom={m.nom} />
              <div className="min-w-0">
                <h2 className="truncate text-base font-bold text-encre">{m.objet || "Sans objet"}</h2>
                <p className="text-sm text-slate-500">
                  {m.nom} ·{" "}
                  <a className="text-marque-700 underline-offset-4 hover:underline" href={"mailto:" + m.email}>{m.email}</a> · {dateHeure(m.cree_le)}
                </p>
              </div>
            </div>
            {m.traite ? <Badge ton="vert">Traité</Badge> : <Badge ton="orange">À traiter</Badge>}
          </div>
          <p className="mt-4 whitespace-pre-wrap rounded-2xl rounded-tl-sm bg-fond p-4 text-sm leading-relaxed">{m.message}</p>
          {!m.traite && (
            <div className="mt-4 flex justify-end">
              <Bouton variante="secondaire" className="gap-1.5" onClick={() => traiter(m.id)}>
                <CheckCheck className="h-4 w-4 text-baobab" aria-hidden="true" />
                Marquer comme traité
              </Bouton>
            </div>
          )}
        </article>
      ))}
      </div>
      {liste && <Pagination {...pageMessages} />}
    </Cadre>
  );
}
