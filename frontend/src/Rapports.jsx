import { useState } from "react";
import { telecharger } from "./api";
import Cadre from "./Cadre.jsx";
import { Alerte, Bouton, Champ, Panneau, classeSaisie } from "./ui.jsx";

const PERIODES = [["jour", "Journalier"], ["mois", "Mensuel"], ["annee", "Annuel"]];

export default function Rapports() {
  const [periode, setPeriode] = useState("mois");
  const [jour, setJour] = useState(new Date().toISOString().slice(0, 10));
  const [format, setFormat] = useState("xlsx");
  const [envoi, setEnvoi] = useState(false);
  const [erreur, setErreur] = useState("");
  const [succes, setSucces] = useState("");

  async function lancer(e) {
    e.preventDefault();
    setErreur("");
    setSucces("");
    setEnvoi(true);
    try {
      const { blob, nom } = await telecharger("/rapports/activite", { periode, jour, format });
      const nomFichier = nom !== "rapport" ? nom : "rapport_activite_" + periode + "_" + jour + "." + format;
      const adresse = URL.createObjectURL(blob);
      const lien = document.createElement("a");
      lien.href = adresse;
      lien.download = nomFichier;
      document.body.appendChild(lien);
      lien.click();
      lien.remove();
      URL.revokeObjectURL(adresse);
      setSucces("Rapport généré : " + nomFichier);
    } catch (err) {
      setErreur(err.message);
    } finally {
      setEnvoi(false);
    }
  }

  return (
    <Cadre titre="Rapports d'activité">
      {erreur && <Alerte>{erreur}</Alerte>}
      {succes && <Alerte ton="succes">{succes}</Alerte>}
      <Panneau titre="Générer un rapport">
        <form className="grid gap-4 sm:grid-cols-3" onSubmit={lancer}>
          <Champ label="Période">
            <select className={classeSaisie} value={periode} onChange={(e) => setPeriode(e.target.value)}>
              {PERIODES.map(([cle, libelle]) => <option key={cle} value={cle}>{libelle}</option>)}
            </select>
          </Champ>
          <Champ label="Un jour de la période" aide="Le rapport couvre la période qui contient cette date.">
            <input className={classeSaisie} type="date" value={jour} required
              onChange={(e) => setJour(e.target.value)} />
          </Champ>
          <Champ label="Format">
            <select className={classeSaisie} value={format} onChange={(e) => setFormat(e.target.value)}>
              <option value="xlsx">Excel (.xlsx)</option>
              <option value="pdf">PDF</option>
            </select>
          </Champ>
          <div className="sm:col-span-3">
            <Bouton type="submit" disabled={envoi}>{envoi ? "Génération…" : "Télécharger le rapport"}</Bouton>
          </div>
        </form>
        <p className="mt-4 text-xs text-slate-500">Chaque génération de rapport est inscrite au journal d'audit.</p>
      </Panneau>
    </Cadre>
  );
}
