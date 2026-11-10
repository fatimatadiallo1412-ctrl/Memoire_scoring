import { useEffect, useState } from "react";
import { appeler } from "./api";
import { LIBELLE_CATEGORIE } from "./listes.js";
import { invaliderMetiers } from "./metiers.js";
import Cadre from "./Cadre.jsx";
import { Alerte, Bouton, Chargement, Panneau, classeSaisie } from "./ui.jsx";

export default function Metiers() {
  const [aClasser, setAClasser] = useState([]);
  const [categories, setCategories] = useState([]);
  const [choix, setChoix] = useState({});
  const [erreur, setErreur] = useState("");
  const [message, setMessage] = useState("");
  const [chargement, setChargement] = useState(true);

  useEffect(() => {
    Promise.all([appeler("/professions/a-classer"), appeler("/professions/categories")])
      .then(([liste, cats]) => {
        setAClasser(liste);
        setCategories(cats);
      })
      .catch((e) => setErreur(e.message))
      .finally(() => setChargement(false));
  }, []);

  async function classer(metier) {
    setErreur("");
    setMessage("");
    try {
      await appeler("/professions/" + metier.code, {
        methode: "PUT",
        json: { categorie_modele: choix[metier.code] },
      });
      invaliderMetiers();
      setAClasser((liste) => liste.filter((m) => m.code !== metier.code));
      setMessage(
        "« " + metier.libelle + " » est classé. Les scores en cours des " + metier.nb_clients +
          " client(s) concerné(s) doivent être recalculés."
      );
    } catch (e) {
      setErreur(e.message);
    }
  }

  return (
    <Cadre titre="Métiers à classer">
      <Alerte ton="info">
        Un métier saisi librement n'a pas de catégorie pour le modèle. Tant qu'il n'est pas classé, le score des
        clients concernés utilise « Non renseigné ». Choisissez la catégorie la plus proche.
      </Alerte>
      {erreur && <Alerte>{erreur}</Alerte>}
      {message && <Alerte ton="succes">{message}</Alerte>}
      {chargement && <Chargement />}
      {!chargement && aClasser.length === 0 && (
        <Panneau><p className="text-sm text-slate-600">Aucun métier à classer.</p></Panneau>
      )}
      {aClasser.length > 0 && (
        <Panneau>
          <div className="divide-y divide-slate-100">
            {aClasser.map((m) => (
              <div key={m.code}
                className="grid gap-3 py-3 first:pt-0 last:pb-0 md:grid-cols-[1fr_16rem_auto] md:items-center">
                <div>
                  <p className="font-medium text-slate-900">{m.libelle}</p>
                  <p className="text-xs text-slate-500">{m.nb_clients} client(s) concerné(s)</p>
                </div>
                <select className={classeSaisie} aria-label={"Catégorie pour " + m.libelle}
                  value={choix[m.code] || ""}
                  onChange={(e) => setChoix({ ...choix, [m.code]: e.target.value })}>
                  <option value="">Choisir une catégorie…</option>
                  {categories.map((c) => (
                    <option key={c} value={c}>{(LIBELLE_CATEGORIE[c] || c) + " (" + c + ")"}</option>
                  ))}
                </select>
                <Bouton disabled={!choix[m.code]} onClick={() => classer(m)}>Classer</Bouton>
              </div>
            ))}
          </div>
        </Panneau>
      )}
    </Cadre>
  );
}
