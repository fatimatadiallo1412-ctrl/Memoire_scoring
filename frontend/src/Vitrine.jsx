import { useState } from "react";
import { Link, NavLink } from "react-router-dom";
import { useAuth } from "./auth.jsx";
import { ACCUEIL } from "./roles.js";
import { MARQUE } from "./marque.js";

const LIENS = [["/", "Accueil"], ["/produits", "Nos produits"], ["/contact", "Contactez-nous"]];

export function Marque({ clair = false }) {
  return (
    <Link to="/" className="flex items-center gap-2" aria-label={"Accueil " + MARQUE.nom}>
      <span className="flex h-9 w-9 items-center justify-center rounded-full bg-marque-700 text-lg font-bold text-white">
        {MARQUE.nom.charAt(0)}
      </span>
      <span className={"text-xl font-semibold " + (clair ? "text-white" : "text-marque-700")}>{MARQUE.nom}</span>
    </Link>
  );
}

export default function Vitrine({ children }) {
  const { utilisateur } = useAuth();
  const [ouvert, setOuvert] = useState(false);

  const classeLien = ({ isActive }) =>
    "rounded-md px-3 py-2 text-sm font-medium transition " +
    (isActive ? "text-marque-700" : "text-slate-600 hover:text-marque-700");

  const bouton = utilisateur ? (
    <Link to={ACCUEIL[utilisateur.role]}
      className="inline-flex justify-center rounded-md bg-marque-700 px-4 py-2 text-sm font-medium text-white hover:bg-marque-800">
      Mon espace
    </Link>
  ) : (
    <Link to="/connexion"
      className="inline-flex justify-center rounded-md bg-marque-700 px-4 py-2 text-sm font-medium text-white hover:bg-marque-800">
      Connexion
    </Link>
  );

  const menu = LIENS.map(([chemin, libelle]) => (
    <NavLink key={chemin} to={chemin} end={chemin === "/"} className={classeLien} onClick={() => setOuvert(false)}>
      {libelle}
    </NavLink>
  ));

  return (
    <div className="flex min-h-screen flex-col bg-white text-slate-800">
      <header className="sticky top-0 z-10 border-b border-slate-200 bg-white/95 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-4 py-3">
          <Marque />
          <nav className="hidden items-center gap-1 md:flex">{menu}</nav>
          <div className="hidden md:block">{bouton}</div>
          <button type="button" className="rounded-md p-2 text-slate-700 hover:bg-slate-100 md:hidden"
            aria-label="Ouvrir le menu" aria-expanded={ouvert} onClick={() => setOuvert(!ouvert)}>
            <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
              {ouvert
                ? <path strokeLinecap="round" strokeLinejoin="round" d="M6 6l12 12M6 18L18 6" />
                : <path strokeLinecap="round" strokeLinejoin="round" d="M4 6h16M4 12h16M4 18h16" />}
            </svg>
          </button>
        </div>
        {ouvert && (
          <div className="grid gap-1 border-t border-slate-200 px-4 pb-4 pt-2 md:hidden">
            {menu}
            <div className="mt-2">{bouton}</div>
          </div>
        )}
      </header>

      <main className="flex-1">{children}</main>

      <footer className="bg-slate-900 text-slate-300">
        <div className="mx-auto grid max-w-6xl gap-6 px-4 py-8 sm:grid-cols-3">
          <div>
            <Marque clair />
            <p className="mt-3 text-sm">{MARQUE.slogan}</p>
          </div>
          <div className="text-sm">
            <h3 className="mb-2 font-semibold text-white">Navigation</h3>
            <ul className="space-y-1">
              {LIENS.map(([chemin, libelle]) => (
                <li key={chemin}><Link className="hover:text-white" to={chemin}>{libelle}</Link></li>
              ))}
              <li><Link className="hover:text-white" to="/connexion">Connexion</Link></li>
            </ul>
          </div>
          <div className="text-sm">
            <h3 className="mb-2 font-semibold text-white">Contact</h3>
            <p>{MARQUE.adresse}</p>
            <p>{MARQUE.telephone}</p>
            <p>{MARQUE.email}</p>
          </div>
        </div>
        <p className="border-t border-slate-800 py-4 text-center text-xs text-slate-500">
          © {new Date().getFullYear()} {MARQUE.nom} · Projet de mémoire de Master 2 MIAGE
        </p>
      </footer>
    </div>
  );
}
