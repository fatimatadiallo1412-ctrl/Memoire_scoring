import { useCallback, useEffect, useState } from "react";
import { appeler } from "./api";
import { useAuth } from "./auth.jsx";
import { dateFr } from "./formats.js";
import Cadre from "./Cadre.jsx";
import { Alerte, Bouton, Chargement, Panneau, classeSaisie } from "./ui.jsx";

// Affichage et bornes saisissables. Les bornes réelles sont celles de l'API (qui a le dernier mot) ;
// elles sont répétées ici seulement pour prévenir l'utilisateur avant l'envoi.
const META = {
  seuil_defaut: { libelle: "Seuil de défaut accepté", unite: "%", echelle: 100, min: 1, max: 60, pas: "0.1" },
  endettement_max: { libelle: "Endettement maximal", unite: "% du revenu", echelle: 100, min: 10, max: 80, pas: "1" },
  ratio_min: { libelle: "Réduction minimale proposable", unite: "% du montant demandé", echelle: 100, min: 10, max: 100, pas: "1" },
  pas_montant: { libelle: "Pas de réduction du montant", unite: "FCFA", echelle: 1, min: 1000, max: 1000000, pas: "1000" },
  facteur_prudence_antecedent: { libelle: "Facteur de prudence (incident passé régularisé)", unite: "coefficient (1 = désactivé)", echelle: 1, min: 0.1, max: 1, pas: "0.05" },
};

function metaDe(cle) {
  return META[cle] || { libelle: cle, unite: "", echelle: 1, min: -Infinity, max: Infinity, pas: "any" };
}

function afficher(cle, valeur) {
  return String(Math.round(valeur * metaDe(cle).echelle * 1000) / 1000);
}

export default function Parametres() {
  const { utilisateur } = useAuth();
  const peutModifier = utilisateur.role === "decideur";
  const [liste, setListe] = useState(null);
  const [saisies, setSaisies] = useState({});
  const [erreur, setErreur] = useState("");
  const [succes, setSucces] = useState("");
  const [occupe, setOccupe] = useState("");

  const charger = useCallback(async () => {
    try {
      const donnees = await appeler("/parametres");
      setListe(donnees);
      setSaisies(Object.fromEntries(donnees.map((p) => [p.cle, afficher(p.cle, p.valeur)])));
    } catch (e) {
      setErreur(e.message);
    }
  }, []);

  useEffect(() => {
    charger();
  }, [charger]);

  async function enregistrer(p) {
    setErreur("");
    setSucces("");
    const m = metaDe(p.cle);
    const saisie = Number(saisies[p.cle]);
    if (saisies[p.cle] === "" || Number.isNaN(saisie) || saisie < m.min || saisie > m.max) {
      setErreur(m.libelle + " : saisissez une valeur entre " + m.min + " et " + m.max + " (" + m.unite + ").");
      return;
    }
    setOccupe(p.cle);
    try {
      await appeler("/parametres/" + p.cle, {
        methode: "PUT",
        json: { valeur: Math.round((saisie / m.echelle) * 1e6) / 1e6 },
      });
      await charger();
      setSucces(m.libelle + " : valeur enregistrée.");
    } catch (e) {
      setErreur(e.message);
    } finally {
      setOccupe("");
    }
  }

  return (
    <Cadre titre="Paramètres de la politique de crédit">
      <Alerte ton="info">
        Ces règles pilotent la recommandation du modèle. Chaque modification est inscrite au journal d'audit avec
        l'ancienne et la nouvelle valeur.
        {peutModifier ? "" : " Seul le directeur peut les modifier."}
      </Alerte>
      {erreur && <Alerte>{erreur}</Alerte>}
      {succes && <Alerte ton="succes">{succes}</Alerte>}
      {!liste && !erreur && <Chargement />}
      {liste && (
        <Panneau>
          <div className="divide-y divide-slate-100">
            {liste.map((p) => {
              const m = metaDe(p.cle);
              const modifie = saisies[p.cle] !== afficher(p.cle, p.valeur);
              return (
                <div key={p.cle} className="grid gap-3 py-4 first:pt-0 last:pb-0 md:grid-cols-[1fr_auto] md:items-center">
                  <div>
                    <h3 className="font-semibold text-slate-900">{m.libelle}</h3>
                    <p className="text-sm text-slate-600">{p.description}</p>
                    <p className="mt-0.5 text-xs text-slate-400">
                      {p.modifie_le ? "Modifié le " + dateFr(p.modifie_le.slice(0, 10)) : "Valeur par défaut"}
                    </p>
                  </div>
                  <div className="flex flex-wrap items-center gap-2">
                    <input className={classeSaisie + " !w-28"} type="number" step={m.pas} min={m.min} max={m.max}
                      value={saisies[p.cle] ?? ""} disabled={!peutModifier}
                      onChange={(e) => { setSucces(""); setSaisies({ ...saisies, [p.cle]: e.target.value }); }} />
                    <span className="text-xs text-slate-500">{m.unite}</span>
                    {peutModifier && (
                      <Bouton disabled={!modifie || occupe === p.cle} onClick={() => enregistrer(p)}>
                        {occupe === p.cle ? "…" : "Enregistrer"}
                      </Bouton>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </Panneau>
      )}
    </Cadre>
  );
}
