import { useEffect, useState } from "react";
import { ArrowRight, Mail, MapPin, Menu, Phone, X } from "lucide-react";
import { Link, NavLink } from "react-router-dom";
import { useAuth } from "./auth.jsx";
import LogoMarque from "./LogoMarque.jsx";
import { ACCUEIL } from "./roles.js";
import { MARQUE } from "./marque.js";

const LIENS = [["/", "Accueil"], ["/produits", "Nos produits"], ["/contact", "Contactez-nous"]];

export function Marque({ clair = false }) {
  return (
    <Link to="/" className="group flex items-center gap-2.5" aria-label={"Accueil " + MARQUE.nom}>
      <LogoMarque className="h-9 w-9 transition-transform duration-300 ease-out motion-safe:group-hover:-rotate-6" clair={clair} />
      <span className={"font-display text-xl font-bold tracking-tight " + (clair ? "text-white" : "text-encre")}>{MARQUE.nom}</span>
    </Link>
  );
}

const BOUTON =
  "inline-flex min-h-11 items-center justify-center gap-2 rounded-full px-5 text-sm font-semibold transition duration-200 ease-out ";
const PRIMAIRE = BOUTON + "bg-marque-700 text-white shadow-sm hover:bg-marque-800 hover:shadow-md motion-safe:hover:-translate-y-0.5";
const SECONDAIRE = BOUTON + "text-encre hover:bg-fond";

export default function Vitrine({ children }) {
  const { utilisateur } = useAuth();
  const [ouvert, setOuvert] = useState(false);
  const [defile, setDefile] = useState(false);

  // L'en-tête prend une ombre dès que la page défile.
  useEffect(() => {
    const surDefilement = () => setDefile(window.scrollY > 8);
    surDefilement();
    window.addEventListener("scroll", surDefilement, { passive: true });
    return () => window.removeEventListener("scroll", surDefilement);
  }, []);

  const classeLien = ({ isActive }) =>
    "flex min-h-10 items-center rounded-full px-4 text-sm font-medium transition duration-200 " +
    (isActive ? "bg-white text-marque-700 shadow-sm" : "text-texte-doux hover:text-encre");

  const classeLienMobile = ({ isActive }) =>
    "flex min-h-12 items-center rounded-xl px-4 text-base font-medium transition-colors duration-150 " +
    (isActive ? "bg-marque-50 text-marque-700" : "text-encre hover:bg-fond");

  // Connecté : accès à son espace. Sinon : se connecter ou s'inscrire.
  const boutons = utilisateur ? (
    <Link to={ACCUEIL[utilisateur.role]} className={PRIMAIRE + " group"}>
      Mon espace
      <ArrowRight className="h-4 w-4 transition-transform duration-200 group-hover:translate-x-0.5" aria-hidden="true" />
    </Link>
  ) : (
    <>
      <Link to="/connexion" className={SECONDAIRE}>
        Se connecter
      </Link>
      <Link to="/contact" state={{ objet: "Demande d'inscription" }} className={PRIMAIRE + " group"}>
        S'inscrire
        <ArrowRight className="h-4 w-4 transition-transform duration-200 group-hover:translate-x-0.5" aria-hidden="true" />
      </Link>
    </>
  );

  const menu = (classe) =>
    LIENS.map(([chemin, libelle]) => (
      <NavLink key={chemin} to={chemin} end={chemin === "/"} className={classe} onClick={() => setOuvert(false)}>
        {libelle}
      </NavLink>
    ));

  return (
    <div className="flex min-h-screen flex-col bg-white text-texte">
      <header
        className={
          "sticky top-0 z-30 border-b backdrop-blur-md transition duration-300 " +
          (defile || ouvert ? "border-bord bg-white/90 shadow-sm" : "border-transparent bg-fond/80")
        }
      >
        <div className="mx-auto flex h-18 max-w-7xl items-center justify-between gap-4 px-4 sm:px-6">
          <Marque />
          <nav className="hidden items-center gap-1 rounded-full bg-fond p-1 ring-1 ring-inset ring-bord md:flex">
            {menu(classeLien)}
          </nav>
          <div className="hidden items-center gap-1 md:flex">{boutons}</div>
          <button type="button"
            className="flex h-11 w-11 items-center justify-center rounded-full bg-transparent p-0 text-encre ring-1 ring-inset ring-bord transition-colors duration-150 hover:bg-white md:hidden"
            aria-label="Ouvrir le menu" aria-expanded={ouvert} onClick={() => setOuvert(!ouvert)}>
            {ouvert ? <X className="h-5 w-5" aria-hidden="true" /> : <Menu className="h-5 w-5" aria-hidden="true" />}
          </button>
        </div>
        {ouvert && (
          <div className="animate-apparition border-t border-bord bg-white px-4 pb-5 pt-3 md:hidden">
            <nav className="grid gap-1">{menu(classeLienMobile)}</nav>
            <div className="mt-4 grid gap-2 border-t border-bord pt-4 sm:grid-cols-2 [&>a]:min-h-12">{boutons}</div>
          </div>
        )}
      </header>

      <main className="flex-1">{children}</main>

      <footer className="bg-encre text-slate-400">
        <div className="mx-auto grid max-w-7xl gap-8 px-4 py-10 sm:px-6 md:grid-cols-12">
          <div className="md:col-span-4">
            <Marque clair />
            <p className="mt-3 max-w-xs text-sm leading-relaxed text-slate-300">{MARQUE.slogan}</p>
          </div>

          <div className="md:col-span-3">
            <h3 className="mb-3 text-sm font-semibold text-white">Navigation</h3>
            <ul className="space-y-1.5 text-sm">
              {[...LIENS, ["/connexion", "Connexion"]].map(([chemin, libelle]) => (
                <li key={chemin}>
                  <Link to={chemin} className="transition-colors duration-200 hover:text-soleil">{libelle}</Link>
                </li>
              ))}
            </ul>
          </div>

          <div className="md:col-span-5">
            <h3 className="mb-3 text-sm font-semibold text-white">Contact</h3>
            <ul className="space-y-2 text-sm">
              {[[MapPin, MARQUE.adresse], [Phone, MARQUE.telephone], [Mail, MARQUE.email]].map(([Icone, valeur]) => (
                <li key={valeur} className="flex items-start gap-2.5">
                  <Icone className="mt-0.5 h-4 w-4 shrink-0 text-soleil" aria-hidden="true" />
                  <p>{valeur}</p>
                </li>
              ))}
            </ul>
          </div>
        </div>

        <div className="border-t border-white/10">
          <p className="mx-auto max-w-7xl px-4 py-4 text-xs text-slate-500 sm:px-6">
            © {new Date().getFullYear()} {MARQUE.nom} · Projet de mémoire de Master 2 MIAGE
          </p>
        </div>
      </footer>
    </div>
  );
}
