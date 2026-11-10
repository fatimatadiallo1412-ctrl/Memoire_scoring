import { useCallback, useEffect, useState } from "react";
import { appeler } from "./api";
import Cadre from "./Cadre.jsx";
import { Alerte, Bouton, Chargement } from "./ui.jsx";

export default function TableauBord() {
  const [lien, setLien] = useState(null);
  const [erreur, setErreur] = useState("");

  const charger = useCallback(async () => {
    setErreur("");
    setLien(null);
    try {
      const r = await appeler("/tableau-de-bord/lien");
      setLien(r.url);
    } catch (e) {
      setErreur(e.message);
    }
  }, []);

  useEffect(() => {
    charger();
  }, [charger]);

  return (
    <Cadre titre="Tableau de bord"
      actions={<Bouton variante="secondaire" onClick={charger}>Actualiser</Bouton>}>
      {erreur && <Alerte>{erreur}</Alerte>}
      {!lien && !erreur && <Chargement />}
      {lien && (
        <iframe src={lien} title="Tableau de bord"
          className="h-[80vh] w-full rounded-xl bg-white ring-1 ring-slate-200" />
      )}
      <p className="mt-3 text-xs text-slate-500">
        L'accès est personnel et temporaire : il expire après 10 minutes (cliquez sur « Actualiser » pour le renouveler)
        et chaque ouverture est inscrite au journal d'audit.
      </p>
    </Cadre>
  );
}
