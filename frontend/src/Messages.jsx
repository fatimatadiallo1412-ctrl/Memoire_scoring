import { useCallback, useEffect, useState } from "react";
import { appeler } from "./api";
import Cadre from "./Cadre.jsx";
import { Alerte, Badge, Bouton, Chargement, Panneau, classeSaisie } from "./ui.jsx";

function dateHeure(iso) {
  const d = new Date(iso);
  return d.toLocaleDateString("fr-FR") + " à " + d.toLocaleTimeString("fr-FR", { hour: "2-digit", minute: "2-digit" });
}

export default function Messages() {
  const [filtre, setFiltre] = useState("non_traites");
  const [liste, setListe] = useState(null);
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
      <div className="mb-4 max-w-xs">
        <select className={classeSaisie} value={filtre} onChange={(e) => setFiltre(e.target.value)}
          aria-label="Filtrer les messages">
          <option value="non_traites">Non traités</option>
          <option value="tous">Tous les messages</option>
        </select>
      </div>
      {erreur && <Alerte>{erreur}</Alerte>}
      {!liste && !erreur && <Chargement />}
      {liste && liste.length === 0 && <p className="text-sm text-slate-500">Aucun message.</p>}
      {liste && liste.map((m) => (
        <Panneau key={m.id}
          titre={m.objet || "Sans objet"}
          droite={m.traite ? <Badge ton="vert">Traité</Badge> : <Badge ton="orange">À traiter</Badge>}>
          <p className="text-sm text-slate-500">
            {m.nom} ·{" "}
            <a className="text-marque-700 underline" href={"mailto:" + m.email}>{m.email}</a> · {dateHeure(m.cree_le)}
          </p>
          <p className="mt-3 whitespace-pre-wrap text-sm">{m.message}</p>
          {!m.traite && (
            <div className="mt-4">
              <Bouton variante="secondaire" onClick={() => traiter(m.id)}>Marquer comme traité</Bouton>
            </div>
          )}
        </Panneau>
      ))}
    </Cadre>
  );
}
