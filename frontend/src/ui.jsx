const TONS_BADGE = {
  neutre: "bg-slate-100 text-slate-700",
  rouge: "bg-red-100 text-red-700",
  vert: "bg-green-100 text-green-700",
  bleu: "bg-blue-100 text-blue-700",
  orange: "bg-amber-100 text-amber-800",
};

const TONS_ALERTE = {
  erreur: "border-red-200 bg-red-50 text-red-800",
  succes: "border-green-200 bg-green-50 text-green-800",
  info: "border-blue-200 bg-blue-50 text-blue-800",
  attention: "border-amber-200 bg-amber-50 text-amber-900",
};

const VARIANTES = {
  primaire: "bg-marque-700 text-white hover:bg-marque-800 disabled:opacity-50",
  secondaire: "bg-white text-slate-700 ring-1 ring-inset ring-slate-300 hover:bg-slate-50 disabled:opacity-50",
  danger: "bg-red-600 text-white hover:bg-red-700 disabled:opacity-50",
  lien: "text-marque-700 underline hover:text-marque-800 !px-0 !py-0",
};

export const classeSaisie =
  "block w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm shadow-sm placeholder:text-slate-400 focus:border-marque-600 focus:outline-none focus:ring-2 focus:ring-marque-600/30 disabled:bg-slate-100";

export const TH = "whitespace-nowrap px-3 py-2 text-left font-semibold text-slate-600";
export const TD = "px-3 py-2";

export function Bouton({ variante = "primaire", className = "", type = "button", ...reste }) {
  return (
    <button
      type={type}
      className={
        "inline-flex items-center justify-center rounded-md px-4 py-2 text-sm font-medium transition disabled:cursor-not-allowed " +
        VARIANTES[variante] + " " + className
      }
      {...reste}
    />
  );
}

export function Badge({ ton = "neutre", children }) {
  return (
    <span className={"inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium " + TONS_BADGE[ton]}>
      {children}
    </span>
  );
}

export function Alerte({ ton = "erreur", children }) {
  return <div className={"mb-4 rounded-md border px-4 py-3 text-sm " + TONS_ALERTE[ton]}>{children}</div>;
}

export function Panneau({ titre, droite, children, className = "" }) {
  return (
    <section className={"mb-5 rounded-xl bg-white p-4 shadow-sm ring-1 ring-slate-200 sm:p-6 " + className}>
      {(titre || droite) && (
        <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
          {titre && <h2 className="text-lg font-semibold text-slate-900">{titre}</h2>}
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
      {aide && <span className="mt-1 block text-xs text-slate-500">{aide}</span>}
    </label>
  );
}

export function Tableau({ children }) {
  return (
    <div className="overflow-x-auto rounded-lg ring-1 ring-slate-200">
      <table className="min-w-full divide-y divide-slate-200 text-sm">{children}</table>
    </div>
  );
}

export function Infos({ children }) {
  return <dl className="grid grid-cols-1 gap-x-6 gap-y-3 sm:grid-cols-2 lg:grid-cols-3">{children}</dl>;
}

export function Info({ libelle, children }) {
  return (
    <div>
      <dt className="text-xs uppercase tracking-wide text-slate-500">{libelle}</dt>
      <dd className="mt-0.5 font-medium text-slate-900">{children}</dd>
    </div>
  );
}

export function Chargement() {
  return <p className="py-6 text-center text-sm text-slate-500">Chargement…</p>;
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
    <label className="flex items-center gap-2 text-sm text-slate-700">
      <input type="checkbox" className="h-4 w-4 accent-marque-700" checked={checked}
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
    <Link to={to} className={"inline-flex items-center justify-center rounded-md px-4 py-2 text-sm font-medium transition " + style}>
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
    <div className="mb-4 rounded-md border border-amber-300 bg-amber-50 p-4 text-sm text-amber-900">
      <p className="font-semibold">Mot de passe temporaire pour {email}</p>
      <p className="my-2 select-all rounded bg-white px-3 py-2 font-mono text-lg tracking-wider text-slate-900 ring-1 ring-amber-200">
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
