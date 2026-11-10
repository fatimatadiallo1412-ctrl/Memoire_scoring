import { useEffect, useState } from "react";
import { Link, NavLink } from "react-router-dom";
import { MARQUE } from "./marque.js";
import { appeler } from "./api";
import { useAuth } from "./auth.jsx";
import { LIBELLE_ROLE } from "./roles.js";
import { Bouton } from "./ui.jsx";

const LIENS = {
  agent_credit: [["/clients", "Clients"], ["/dossiers", "Dossiers"]],
  administrateur: [["/clients", "Clients"], ["/dossiers", "Dossiers"], ["/metiers", "Métiers"], ["/messages", "Messages"], ["/parametres", "Paramètres"], ["/rapports", "Rapports"], ["/tableau-de-bord", "Tableau de bord"]],
  decideur: [["/dossiers", "Dossiers"], ["/clients", "Clients"], ["/metiers", "Métiers"], ["/parametres", "Paramètres"], ["/rapports", "Rapports"], ["/tableau-de-bord", "Tableau de bord"]],
  client: [["/espace", "Mon espace"], ["/espace/assistant", "Assistant"]],
};

function PastilleRappels() {
  const [nombre, setNombre] = useState(0);
  useEffect(() => {
    let actif = true;
    function charger() {
      appeler("/moi/rappels", { params: { non_lus: "true", limite: 200 } })
        .then((liste) => { if (actif) setNombre(liste.length); })
        .catch(() => {});
    }
    charger();
    window.addEventListener("rappels-maj", charger);
    return () => {
      actif = false;
      window.removeEventListener("rappels-maj", charger);
    };
  }, []);
  return nombre > 0 ? (
    <span className="ml-1.5 inline-flex min-w-5 items-center justify-center rounded-full bg-red-500 px-1.5 text-xs font-semibold text-white">
      {nombre}
    </span>
  ) : null;
}

export default function Cadre({ titre, actions, children }) {
  const { utilisateur, deconnecter } = useAuth();
  const [ouvert, setOuvert] = useState(false);
  const liens = LIENS[utilisateur.role];

  const classeLien = ({ isActive }) =>
    "flex items-center rounded-md px-3 py-2 text-sm font-medium transition " +
    (isActive ? "bg-white/20 text-white" : "text-blue-100 hover:bg-white/10 hover:text-white");

  const menu = liens.map(([chemin, libelle]) => (
    <NavLink key={chemin} to={chemin} className={classeLien} onClick={() => setOuvert(false)}>
      {libelle}
      {utilisateur.role === "client" && chemin === "/espace" && <PastilleRappels />}
    </NavLink>
  ));

  return (
    <div className="min-h-screen bg-slate-100 text-slate-800">
      <header className="bg-marque-700 text-white shadow">
        <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-4 py-3">
          <Link to="/" className="text-base font-semibold hover:text-blue-100 sm:text-lg">{MARQUE.nom}</Link>

          <nav className="hidden flex-1 items-center gap-1 lg:flex">{menu}</nav>

          <div className="hidden items-center gap-3 text-sm lg:flex">
            <span className="text-right leading-tight">
              <span className="block font-medium">{utilisateur.nom_complet}</span>
              <span className="block text-xs text-blue-200">{LIBELLE_ROLE[utilisateur.role]}</span>
            </span>
            <Bouton variante="secondaire" onClick={deconnecter}>Déconnexion</Bouton>
          </div>

          <button
            type="button"
            className="rounded-md p-2 hover:bg-white/10 lg:hidden"
            aria-label="Ouvrir le menu"
            aria-expanded={ouvert}
            onClick={() => setOuvert(!ouvert)}
          >
            <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
              {ouvert
                ? <path strokeLinecap="round" strokeLinejoin="round" d="M6 6l12 12M6 18L18 6" />
                : <path strokeLinecap="round" strokeLinejoin="round" d="M4 6h16M4 12h16M4 18h16" />}
            </svg>
          </button>
        </div>

        {ouvert && (
          <div className="border-t border-white/20 px-4 pb-4 pt-2 lg:hidden">
            <nav className="grid gap-1">{menu}</nav>
            <div className="mt-3 flex items-center justify-between gap-3 border-t border-white/20 pt-3 text-sm">
              <span>
                <span className="block font-medium">{utilisateur.nom_complet}</span>
                <span className="block text-xs text-blue-200">{LIBELLE_ROLE[utilisateur.role]}</span>
              </span>
              <Bouton variante="secondaire" onClick={deconnecter}>Déconnexion</Bouton>
            </div>
          </div>
        )}
      </header>

      <main className="mx-auto max-w-6xl px-4 py-6">
        <div className="mb-5 flex flex-wrap items-center justify-between gap-3">
          <h1 className="text-2xl font-semibold text-slate-900">{titre}</h1>
          {actions}
        </div>
        {children}
      </main>
    </div>
  );
}
