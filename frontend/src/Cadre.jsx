import { useEffect, useState } from "react";
import {
  Briefcase, FileText, FolderOpen, House, KeyRound, LayoutDashboard, LogOut, Mail, Menu, MessageCircle, Settings,
  UserCog, Users, X,
} from "lucide-react";
import LogoMarque from "./LogoMarque.jsx";
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
    <span className="ml-1.5 inline-flex min-w-5 animate-apparition items-center justify-center rounded-full bg-terre px-1.5 text-xs font-semibold text-white">
      {nombre}
    </span>
  ) : null;
}

// Icône de chaque rubrique du menu.
const ICONES = {
  "/clients": Users,
  "/dossiers": FolderOpen,
  "/metiers": Briefcase,
  "/parametres": Settings,
  "/rapports": FileText,
  "/tableau-de-bord": LayoutDashboard,
  "/comptes": UserCog,
  "/reinitialisations": KeyRound,
  "/messages": Mail,
  "/espace": House,
  "/espace/assistant": MessageCircle,
};

function initiales(nom) {
  return (nom || "")
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((mot) => mot[0].toUpperCase())
    .join("");
}

export default function Cadre({ titre, actions, children }) {
  const { utilisateur, deconnecter } = useAuth();
  const [ouvert, setOuvert] = useState(false);
  const liens = LIENS[utilisateur.role];

  // Le tiroir mobile se ferme avec Échap.
  useEffect(() => {
    if (!ouvert) return undefined;
    const surTouche = (e) => { if (e.key === "Escape") setOuvert(false); };
    window.addEventListener("keydown", surTouche);
    return () => window.removeEventListener("keydown", surTouche);
  }, [ouvert]);

  const classeLien = ({ isActive }) =>
    "group relative flex min-h-11 items-center gap-3 rounded-xl px-3 text-sm font-medium transition duration-200 " +
    (isActive ? "bg-marque-700 text-white shadow-md" : "text-texte-doux hover:bg-fond hover:text-encre");

  const menu = liens.map(([chemin, libelle]) => {
    const Icone = ICONES[chemin] || FolderOpen;
    return (
      <NavLink key={chemin} to={chemin} className={classeLien} onClick={() => setOuvert(false)}>
        <Icone className="h-5 w-5 shrink-0 transition-transform duration-200 motion-safe:group-hover:scale-110" aria-hidden="true" />
        <span className="flex-1">{libelle}</span>
        {utilisateur.role === "client" && chemin === "/espace" && <PastilleRappels />}
      </NavLink>
    );
  });

  const profil = (
    <div className="rounded-2xl bg-fond p-3 ring-1 ring-inset ring-bord">
      <div className="flex items-center gap-3">
        <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-soleil font-display text-sm font-bold text-encre" aria-hidden="true">
          {initiales(utilisateur.nom_complet)}
        </span>
        <span className="min-w-0 leading-tight">
          <span className="block truncate text-sm font-semibold text-encre">{utilisateur.nom_complet}</span>
          <span className="block truncate text-xs text-texte-doux">{LIBELLE_ROLE[utilisateur.role]}</span>
        </span>
      </div>
      <Bouton variante="secondaire" className="mt-3 w-full gap-2" onClick={deconnecter}>
        <LogOut className="h-4 w-4" aria-hidden="true" />
        Déconnexion
      </Bouton>
    </div>
  );

  const marque = (
    <Link to="/" className="group flex items-center gap-2.5">
      <LogoMarque className="h-9 w-9 transition-transform duration-300 motion-safe:group-hover:-rotate-6" />
      <span className="font-display text-lg font-bold tracking-tight text-encre">{MARQUE.nom}</span>
    </Link>
  );

  return (
    <div className="min-h-screen bg-fond text-texte">
      {/* Menu latéral (grand écran) */}
      <aside className="fixed inset-y-0 left-0 z-40 hidden w-64 flex-col border-r border-bord bg-white px-4 py-5 lg:flex">
        <div className="px-2">{marque}</div>
        <nav className="mt-8 grid gap-1">{menu}</nav>
        <div className="mt-auto">{profil}</div>
      </aside>

      {/* Barre supérieure (mobile et tablette) */}
      <header className="sticky top-0 z-40 border-b border-bord bg-white/90 backdrop-blur-md lg:hidden">
        <div className="flex h-16 items-center justify-between gap-4 px-4">
          {marque}
          <button
            type="button"
            className="flex h-11 w-11 items-center justify-center rounded-full bg-transparent p-0 text-encre ring-1 ring-inset ring-bord transition-colors duration-150 hover:bg-fond"
            aria-label="Ouvrir le menu"
            aria-expanded={ouvert}
            onClick={() => setOuvert(!ouvert)}
          >
            {ouvert ? <X className="h-5 w-5" aria-hidden="true" /> : <Menu className="h-5 w-5" aria-hidden="true" />}
          </button>
        </div>
      </header>

      {/* Tiroir mobile */}
      {ouvert && (
        <div className="fixed inset-0 z-50 lg:hidden">
          <div className="absolute inset-0 animate-apparition bg-encre/40" onClick={() => setOuvert(false)} aria-hidden="true" />
          <div className="absolute inset-y-0 left-0 flex w-72 max-w-[85vw] animate-tiroir flex-col bg-white px-4 py-5 shadow-2xl">
            <div className="flex items-center justify-between px-2">
              {marque}
              <button type="button" aria-label="Fermer le menu" onClick={() => setOuvert(false)}
                className="flex h-10 w-10 items-center justify-center rounded-full bg-transparent p-0 text-encre transition-colors hover:bg-fond">
                <X className="h-5 w-5" aria-hidden="true" />
              </button>
            </div>
            <nav className="mt-8 grid gap-1">{menu}</nav>
            <div className="mt-auto">{profil}</div>
          </div>
        </div>
      )}

      <div className="lg:pl-64">
        <main key={titre} className="mx-auto max-w-6xl animate-apparition px-4 py-6 sm:px-8 sm:py-10">
          <div className="mb-7 flex flex-wrap items-end justify-between gap-4">
            <div>
              <span className="mb-3 block h-1.5 w-8 rounded-full bg-soleil" aria-hidden="true" />
              <h1 className="text-[clamp(1.6rem,1.3rem+1vw,2.1rem)] font-extrabold leading-tight text-encre">{titre}</h1>
            </div>
            {actions}
          </div>
          {children}
        </main>
      </div>
    </div>
  );
}
