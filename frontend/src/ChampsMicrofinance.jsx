import { OUI_NON, USAGES_MOBILE_MONEY } from "./listes.js";
import { Champ, Liste, classeSaisie } from "./ui.jsx";

// Champs facultatifs propres à la microfinance (voir microfinance.js).
export default function ChampsMicrofinance({ f, changer }) {
  return (
    <fieldset className="grid min-w-0 gap-4 rounded-carte border border-dashed border-bord p-4 sm:col-span-2 sm:grid-cols-2">
      <legend className="px-1 text-sm font-semibold text-encre">Informations microfinance (facultatives)</legend>
      <p className="-mt-1 text-xs text-texte-doux sm:col-span-2">
        Elles ne changent pas le score actuel. Elles permettront d'améliorer le modèle avec les données de l'institution.
      </p>
      <Champ label="Épargne mensuelle (FCFA)">
        <input className={classeSaisie} type="number" min="0" value={f.epargne_mensuelle}
          onChange={(e) => changer("epargne_mensuelle", e.target.value)} />
      </Champ>
      <Champ label="Membre d'une tontine ou d'un groupement">
        <Liste valeur={f.membre_groupement} options={OUI_NON} facultatif
          onChange={(v) => changer("membre_groupement", v)} />
      </Champ>
      <Champ label="Usage du mobile money">
        <Liste valeur={f.usage_mobile_money} options={USAGES_MOBILE_MONEY} facultatif
          onChange={(v) => changer("usage_mobile_money", v)} />
      </Champ>
      <Champ label="Activité saisonnière (revenus irréguliers dans l'année)">
        <Liste valeur={f.activite_saisonniere} options={OUI_NON} facultatif
          onChange={(v) => changer("activite_saisonniere", v)} />
      </Champ>
    </fieldset>
  );
}
