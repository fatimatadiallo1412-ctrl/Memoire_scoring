import {
  Bell, Clock, FolderOpen, LayoutDashboard, Search, Settings, ShieldCheck, TrendingUp, Users,
} from "lucide-react";
import CarteScoring from "./CarteScoring.jsx";
import LogoMarque from "./LogoMarque.jsx";
import { Avatar } from "./ui.jsx";

// Maquette de tableau de bord affichée dans le hero (données d'exemple, non interactive).
const INDICATEURS = [
  { icone: FolderOpen, libelle: "Dossiers analysés", valeur: "128", ton: "bg-marque-50 text-marque-700" },
  { icone: TrendingUp, libelle: "Taux d'accord", valeur: "76 %", ton: "bg-baobab-50 text-baobab" },
  { icone: Clock, libelle: "Délai moyen", valeur: "4 min", ton: "bg-soleil-50 text-soleil-fonce" },
];

const SEMAINE = [["L", 46], ["M", 62], ["M", 54], ["J", 78], ["V", 90], ["S", 38]];

const DOSSIERS = [
  { nom: "Fatou Sarr", activite: "Commerçante", decision: "Accordé", ton: "bg-baobab-50 text-baobab" },
  { nom: "Mariama Ba", activite: "Restauratrice", decision: "À étudier", ton: "bg-soleil-50 text-soleil-fonce" },
  { nom: "Khady Diop", activite: "Vendeuse de tissus", decision: "Accordé", ton: "bg-baobab-50 text-baobab" },
];

const MENU = [LayoutDashboard, Users, FolderOpen, ShieldCheck, Settings];

export default function TableauBordDemo() {
  return (
    <div className="overflow-clip rounded-[1.75rem] bg-white shadow-2xl ring-1 ring-bord">
      {/* Barre supérieure */}
      <div className="flex items-center gap-4 border-b border-bord px-4 py-3 sm:px-5">
        <LogoMarque className="h-7 w-7" />
        <div className="hidden h-9 flex-1 items-center gap-2 rounded-xl bg-fond px-3 text-sm text-texte-doux sm:flex" aria-hidden="true">
          <Search className="h-4 w-4" />
          <span className="block h-2 w-32 rounded-full bg-bord" />
        </div>
        <div className="ml-auto flex items-center gap-3">
          <span className="relative flex h-9 w-9 items-center justify-center rounded-xl bg-fond text-texte-doux" aria-hidden="true">
            <Bell className="h-4 w-4" />
            <span className="absolute right-2 top-2 h-2 w-2 rounded-full bg-terre" />
          </span>
          <Avatar nom="Moussa Fall" taille="h-9 w-9 text-xs" />
        </div>
      </div>

      <div className="flex">
        {/* Menu latéral */}
        <nav className="hidden w-16 shrink-0 flex-col items-center gap-2 border-r border-bord py-5 md:flex" aria-hidden="true">
          {MENU.map((Icone, i) => (
            <span key={i} className={"flex h-10 w-10 items-center justify-center rounded-xl " +
              (i === 0 ? "bg-marque-700 text-white shadow-md" : "text-texte-doux")}>
              <Icone className="h-5 w-5" />
            </span>
          ))}
        </nav>

        <div className="min-w-0 flex-1 bg-fond/60 p-4 sm:p-5">
          <p className="font-display text-base font-bold text-encre">Tableau de bord</p>

          {/* Indicateurs */}
          <div className="mt-3 grid grid-cols-3 gap-3">
            {INDICATEURS.map(({ icone: Icone, libelle, valeur, ton }, i) => (
              <div key={libelle} className="animate-apparition rounded-2xl border border-bord bg-white p-3 sm:p-4"
                style={{ animationDelay: 0.2 + i * 0.1 + "s" }}>
                <span className={"flex h-8 w-8 items-center justify-center rounded-lg " + ton}>
                  <Icone className="h-4 w-4" aria-hidden="true" />
                </span>
                <p className="mt-2 font-display text-xl font-extrabold leading-none text-encre sm:text-2xl">{valeur}</p>
                <p className="mt-1 text-[0.7rem] leading-tight text-texte-doux sm:text-xs">{libelle}</p>
              </div>
            ))}
          </div>

          <div className="mt-4 grid gap-4 lg:grid-cols-[1.15fr_1fr]">
            <CarteScoring />

            <div className="hidden gap-4 sm:grid">
              {/* Graphique */}
              <div className="rounded-2xl border border-bord bg-white p-4">
                <p className="text-sm font-semibold text-encre">Décisions de la semaine</p>
                <div className="mt-4 flex h-24 justify-between gap-2">
                  {SEMAINE.map(([jour, hauteur], i) => (
                    <div key={i} className="flex flex-1 flex-col items-center gap-1.5">
                      <div className="flex w-full flex-1 items-end">
                        <span className={"block w-full origin-bottom animate-pousser rounded-t-md " + (i === 4 ? "bg-marque-700" : "bg-marque-200")}
                          style={{ height: hauteur + "%", animationDelay: 0.5 + i * 0.08 + "s" }} />
                      </div>
                      <span className="text-[0.7rem] text-texte-doux">{jour}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Derniers dossiers */}
              <div className="rounded-2xl border border-bord bg-white p-4">
                <p className="text-sm font-semibold text-encre">Derniers dossiers</p>
                <ul className="mt-3 space-y-3">
                  {DOSSIERS.map(({ nom, activite, decision, ton }, i) => (
                    <li key={nom} className="flex animate-apparition items-center gap-3" style={{ animationDelay: 0.8 + i * 0.12 + "s" }}>
                      <Avatar nom={nom} taille="h-8 w-8 text-[0.7rem]" />
                      <div className="min-w-0 flex-1">
                        <p className="truncate text-sm font-medium text-encre">{nom}</p>
                        <p className="truncate text-xs text-texte-doux">{activite}</p>
                      </div>
                      <span className={"shrink-0 rounded-full px-2.5 py-0.5 text-xs font-semibold " + ton}>{decision}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
