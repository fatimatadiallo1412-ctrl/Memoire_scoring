import { useId } from "react";
import { useMetiers } from "./metiers.js";
import { classeSaisie } from "./ui.jsx";

// Champ libre avec suggestions : on peut choisir un métier de la liste ou écrire le sien.
export default function ChampMetier({ valeur, onChange, metiers }) {
  const identifiant = useId();
  const deLaListe = useMetiers();
  const liste = metiers || deLaListe;
  return (
    <>
      <input
        className={classeSaisie}
        list={identifiant}
        value={valeur}
        onChange={(e) => onChange(e.target.value)}
        maxLength={60}
        autoComplete="off"
        placeholder="Choisir dans la liste ou écrire un métier"
      />
      <datalist id={identifiant}>
        {liste.map((m) => (
          <option key={m.code} value={m.libelle} />
        ))}
      </datalist>
    </>
  );
}
