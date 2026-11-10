import { CircleCheck, CircleX, TriangleAlert } from "lucide-react";

const TONS_BADGE = {
  neutre: "bg-slate-100 text-slate-700",
  rouge: "bg-risque-eleve-fond text-risque-eleve",
  vert: "bg-risque-faible-fond text-risque-faible",
  bleu: "bg-marque-100 text-marque-700",
  orange: "bg-risque-moyen-fond text-risque-moyen",
};

// Une forme accompagne la couleur : l'information ne repose jamais sur la couleur seule.
const ICONE_BADGE = { vert: CircleCheck, orange: TriangleAlert, rouge: CircleX };

const TONS_ALERTE = {
  erreur: "border-red-200 bg-risque-eleve-fond text-risque-eleve",
  succes: "border-green-200 bg-risque-faible-fond text-risque-faible",
  info: "border-marque-100 bg-marque-50 text-marque-800",
  attention: "border-amber-200 bg-risque-moyen-fond text-risque-moyen",
};

const ICONE_ALERTE = { erreur: CircleX, succes: CircleCheck, attention: TriangleAlert };

const VARIANTES = {
  primaire: "bg-marque-700 text-white hover:bg-marque-800 active:bg-marque-800",
  secondaire: "bg-white text-slate-700 ring-1 ring-inset ring-slate-300 hover:bg-slate-50 active:bg-slate-100",
  danger: "bg-risque-eleve text-white hover:bg-red-900 active:bg-red-900",
  lien: "text-marque-700 underline hover:text-marque-800 !px-0 !py-0 !min-h-0",
};

export const classeSaisie =
  "block w-full min-h-11 rounded-champ border border-slate-300 bg-white px-3 py-2 text-base placeholder:text-slate-400 transition-colors duration-150 hover:border-slate-400 focus:border-marque-600 focus:outline-none focus:ring-2 focus:ring-marque-600/30 disabled:bg-slate-100 sm:text-sm";

export const TH = "whitespace-nowrap bg-slate-50 px-3 py-2.5 text-left font-semibold text-texte-doux";
export const TD = "px-3 py-2.5";

export function Bouton({ variante = "primaire", className = "", type = "button", ...reste }) {
  return (
    <button
      type={type}
      className={
        "inline-flex min-h-11 items-center justify-center rounded-champ px-4 py-2 text-sm font-medium transition-colors duration-150 disabled:cursor-not-allowed disabled:opacity-50 " +
        VARIANTES[variante] + " " + className
      }
      {...reste}
    />
  );
}

export function Badge({ ton = "neutre", children }) {
  const Icone = ICONE_BADGE[ton];
  return (
    <span className={"inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-medium " + TONS_BADGE[ton]}>
      {Icone && <Icone className="h-3.5 w-3.5 shrink-0" aria-hidden="true" />}
      {children}
    </span>
  );
}

export function Alerte({ ton = "erreur", children }) {
  const Icone = ICONE_ALERTE[ton];
  return (
    <div
      role={ton === "erreur" ? "alert" : undefined}
      className={"mb-4 flex items-start gap-2.5 rounded-champ border px-4 py-3 text-sm animate-apparition " + TONS_ALERTE[ton]}
    >
      {Icone && <Icone className="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" />}
      <div>{children}</div>
    </div>
  );
}

export function Panneau({ titre, droite, children, className = "" }) {
  return (
    <section className={"mb-5 rounded-carte border border-bord bg-white p-4 animate-apparition sm:p-6 " + className}>
      {(titre || droite) && (
        <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
          {titre && <h2 className="text-sous-titre font-semibold text-texte">{titre}</h2>}
          {droite}
        </div>
      )}
      {children}
    </section>
  );
}

export function Champ({ label, aide, children }) {
  return (
    <label className="block">
      <span className="mb-1 block text-sm font-medium text-slate-700">{label}</span>
      {children}
      {aide && <span className="mt-1 block text-xs text-texte-doux">{aide}</span>}
    </label>
  );
}

export function Tableau({ children }) {
  return (
    <div className="overflow-x-auto rounded-champ border border-bord">
      <table className="min-w-full divide-y divide-slate-200 text-sm [&_tbody_tr]:transition-colors [&_tbody_tr]:duration-150 [&_tbody_tr:hover]:bg-marque-50/60">
        {children}
      </table>
    </div>
  );
}

export function Infos({ children }) {
  return <dl className="grid grid-cols-1 gap-x-6 gap-y-4 sm:grid-cols-2 lg:grid-cols-3">{children}</dl>;
}

export function Info({ libelle, children }) {
  return (
    <div>
      <dt className="text-xs uppercase tracking-wide text-texte-doux">{libelle}</dt>
      <dd className="mt-0.5 font-medium text-texte">{children}</dd>
    </div>
  );
}

// Barres grises animées par opacité (aplats), pour remplacer un écran vide.
export function Squelette({ lignes = 3 }) {
  const largeurs = ["w-3/4", "w-full", "w-2/3", "w-5/6"];
  return (
    <div className="space-y-2.5" aria-hidden="true">
      {Array.from({ length: lignes }, (_, i) => (
        <div key={i} className={"h-4 animate-pulse rounded bg-slate-200 " + largeurs[i % largeurs.length]} />
      ))}
    </div>
  );
}

export function Chargement() {
  return (
    <div role="status" aria-live="polite" className="py-6">
      <p className="mb-3 text-center text-sm text-texte-doux">Chargement…</p>
      <Squelette />
    </div>
  );
}

import { Link } from "react-router-dom";

export function Liste({ valeur, options, onChange, facultatif }) {
  return (
    <select className={classeSaisie} value={valeur} onChange={(e) => onChange(e.target.value)} required={!facultatif}>
      {facultatif && <option value="">(non renseigné)</option>}
      {options.map(([cle, libelle]) => (
        <option key={cle} value={cle}>{libelle}</option>
      ))}
    </select>
  );
}

export function Case({ libelle, checked, onChange }) {
  return (
    <label className="flex min-h-11 items-center gap-2.5 text-sm text-slate-700">
      <input type="checkbox" className="h-5 w-5 accent-marque-700" checked={checked}
        onChange={(e) => onChange(e.target.checked)} />
      {libelle}
    </label>
  );
}

export function LienBouton({ to, variante = "primaire", children }) {
  const style = variante === "primaire"
    ? "bg-marque-700 text-white hover:bg-marque-800"
    : "bg-white text-slate-700 ring-1 ring-inset ring-slate-300 hover:bg-slate-50";
  return (
    <Link to={to} className={"inline-flex min-h-11 items-center justify-center rounded-champ px-4 py-2 text-sm font-medium transition-colors duration-150 " + style}>
      {children}
    </Link>
  );
}

const TONS_DOSSIER = {
  brouillon: "neutre", complet: "neutre", score: "bleu", instruit: "bleu", soumis_decision: "orange",
  accorde: "vert", accorde_modifie: "vert", decaisse: "vert", en_remboursement: "vert", solde: "vert",
  refuse: "rouge", ajourne: "orange", contentieux: "rouge",
};
export function tonDossier(statut) {
  return TONS_DOSSIER[statut] || "neutre";
}

import { useState } from "react";

export function MotDePasseTemp({ email, motDePasse, onFermer }) {
  const [copie, setCopie] = useState(false);
  async function copier() {
    try {
      await navigator.clipboard.writeText(motDePasse);
      setCopie(true);
    } catch {
      // copie impossible : le mot de passe reste affiché
    }
  }
  return (
    <div className="mb-4 rounded-carte border border-amber-300 bg-risque-moyen-fond p-4 text-sm text-risque-moyen animate-apparition">
      <p className="font-semibold">Mot de passe temporaire pour {email}</p>
      <p className="my-2 select-all rounded-champ bg-white px-3 py-2 font-mono text-lg tracking-wider text-texte ring-1 ring-amber-200">
        {motDePasse}
      </p>
      <p>
        Il n'est affiché qu'<strong>une seule fois</strong> et ne peut pas être retrouvé. Communiquez-le à la personne
        après avoir vérifié son identité : elle devra le remplacer à sa première connexion.
      </p>
      <div className="mt-3 flex flex-wrap gap-2">
        <Bouton variante="secondaire" onClick={copier}>{copie ? "Copié" : "Copier"}</Bouton>
        <Bouton variante="secondaire" onClick={onFermer}>J'ai noté le mot de passe, fermer</Bouton>
      </div>
    </div>
  );
}
