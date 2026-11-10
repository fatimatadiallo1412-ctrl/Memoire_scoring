import { useEffect, useState } from "react";
import { Menu, X } from "lucide-react";
import { Link, NavLink } from "react-router-dom";
import { MARQUE } from "./marque.js";
import { appeler } from "./api";
import { useAuth } from "./auth.jsx";
import { LIBELLE_ROLE } from "./roles.js";
import { Bouton } from "./ui.jsx";

const LIENS = {
  agent_credit: [["/clients", "Clients"], ["/dossiers", "Dossiers"]],
  administrateur: [["/comptes", "Comptes"], ["/reinitialisations", "Réinitialisations"], ["/messages", "Messages"]],
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
    "flex min-h-11 items-center rounded-champ px-3 text-sm font-medium transition-colors duration-150 " +
    (isActive ? "bg-white/20 text-white" : "text-blue-100 hover:bg-white/10 hover:text-white");

  const menu = liens.map(([chemin, libelle]) => (
    <NavLink key={chemin} to={chemin} className={classeLien} onClick={() => setOuvert(false)}>
      {libelle}
      {utilisateur.role === "client" && chemin === "/espace" && <PastilleRappels />}
    </NavLink>
  ));

  return (
    <div className="min-h-screen bg-fond text-texte">
      <header className="sticky top-0 z-40 bg-marque-700 text-white">
        <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-4 py-3">
          <Link to="/" className="text-base font-semibold hover:text-blue-100 sm:text-lg">{MARQUE.nom}</Link>

          <nav className="hidden flex-1 items-center gap-1 lg:flex">{menu}</nav>

          <div className="hidden items-center gap-3 text-sm lg:flex">
            <span className="text-right leading-tight">
              <span className="block font-medium">{utilisateur.nom_complet}</span>
              <span className="block text-xs text-blue-200">{LIBELLE_ROLE[utilisateur.role]}</span>
            </span>
            <Link to="/changer-mot-de-passe" className="text-sm text-blue-100 underline hover:text-white" onClick={() => setOuvert(false)}>Mon mot de passe</Link>
            <Bouton variante="secondaire" onClick={deconnecter}>Déconnexion</Bouton>
          </div>

          <button
            type="button"
            className="flex h-11 w-11 items-center justify-center rounded-champ transition-colors duration-150 hover:bg-white/10 lg:hidden"
            aria-label="Ouvrir le menu"
            aria-expanded={ouvert}
            onClick={() => setOuvert(!ouvert)}
          >
            {ouvert ? <X className="h-6 w-6" aria-hidden="true" /> : <Menu className="h-6 w-6" aria-hidden="true" />}
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
              <Link to="/changer-mot-de-passe" className="text-sm text-blue-100 underline hover:text-white" onClick={() => setOuvert(false)}>Mon mot de passe</Link>
            <Bouton variante="secondaire" onClick={deconnecter}>Déconnexion</Bouton>
            </div>
          </div>
        )}
      </header>

      <main className="mx-auto max-w-6xl animate-apparition px-4 py-6 sm:px-6">
        <div className="mb-5 flex flex-wrap items-center justify-between gap-3">
          <h1 className="text-titre font-semibold text-texte">{titre}</h1>
          {actions}
        </div>
        {children}
      </main>
    </div>
  );
}
