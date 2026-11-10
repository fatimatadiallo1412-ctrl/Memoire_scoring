import { useState } from "react";
import { Menu, X } from "lucide-react";
import { Link, NavLink } from "react-router-dom";
import { useAuth } from "./auth.jsx";
import LogoMarque from "./LogoMarque.jsx";
import { ACCUEIL } from "./roles.js";
import { MARQUE } from "./marque.js";

const LIENS = [["/", "Accueil"], ["/produits", "Nos produits"], ["/contact", "Contactez-nous"]];

export function Marque({ clair = false }) {
  return (
    <Link to="/" className="flex items-center gap-2.5" aria-label={"Accueil " + MARQUE.nom}>
      <LogoMarque className="h-9 w-9" clair={clair} />
      <span className={"text-xl font-semibold " + (clair ? "text-white" : "text-marque-700")}>{MARQUE.nom}</span>
    </Link>
  );
}

const BOUTON = "inline-flex min-h-11 items-center justify-center rounded-champ px-4 text-sm font-medium transition-colors duration-150 ";

export default function Vitrine({ children }) {
  const { utilisateur } = useAuth();
  const [ouvert, setOuvert] = useState(false);

  const classeLien = ({ isActive }) =>
    "flex min-h-11 items-center rounded-champ px-3 text-sm font-medium transition-colors duration-150 " +
    (isActive ? "text-marque-700" : "text-slate-600 hover:text-marque-700");

  // Connecté : accès à son espace. Sinon : se connecter ou s'inscrire.
  const boutons = utilisateur ? (
    <Link to={ACCUEIL[utilisateur.role]} className={BOUTON + "bg-marque-700 text-white hover:bg-marque-800"}>
      Mon espace
    </Link>
  ) : (
    <>
      <Link to="/connexion"
        className={BOUTON + "bg-white text-marque-700 ring-1 ring-inset ring-marque-700 hover:bg-marque-50"}>
        Se connecter
      </Link>
      <Link to="/contact" state={{ objet: "Demande d'inscription" }}
        className={BOUTON + "bg-marque-700 text-white hover:bg-marque-800"}>
        S'inscrire
      </Link>
    </>
  );

  const menu = LIENS.map(([chemin, libelle]) => (
    <NavLink key={chemin} to={chemin} end={chemin === "/"} className={classeLien} onClick={() => setOuvert(false)}>
      {libelle}
    </NavLink>
  ));

  return (
    <div className="flex min-h-screen flex-col bg-white text-texte">
      <header className="sticky top-0 z-30 border-b border-bord bg-white">
        <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-4 py-3">
          <Marque />
          <nav className="hidden items-center gap-1 md:flex">{menu}</nav>
          <div className="hidden items-center gap-2 md:flex">{boutons}</div>
          <button type="button"
            className="flex h-11 w-11 items-center justify-center rounded-champ bg-transparent p-0 text-slate-700 transition-colors duration-150 hover:bg-slate-100 md:hidden"
            aria-label="Ouvrir le menu" aria-expanded={ouvert} onClick={() => setOuvert(!ouvert)}>
            {ouvert ? <X className="h-6 w-6" aria-hidden="true" /> : <Menu className="h-6 w-6" aria-hidden="true" />}
          </button>
        </div>
        {ouvert && (
          <div className="grid gap-1 border-t border-bord px-4 pb-4 pt-2 md:hidden">
            {menu}
            <div className="mt-2 grid gap-2 sm:grid-cols-2">{boutons}</div>
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
