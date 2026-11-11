import { useState } from "react";
import { BadgeCheck, Banknote, History, MapPin, Scissors, Sparkles, Wallet } from "lucide-react";

// Carte de démonstration du hero : cliente fictive, données d'exemple.
const PD = 8.2; // probabilité de défaut (%)
const RAYON = 54;
const CIRCONFERENCE = 2 * Math.PI * RAYON;

// Photo de démonstration : déposer le fichier dans frontend/public/images/.
export const PHOTO_CLIENTE = "/images/cliente-demo.jpg";

const FACTEURS = [
  { icone: History, libelle: "Historique de crédit", valeur: 88, ton: "bg-baobab" },
  { icone: Wallet, libelle: "Revenus", valeur: 74, ton: "bg-marque-600" },
  { icone: Banknote, libelle: "Comportement de remboursement", valeur: 93, ton: "bg-baobab" },
];

// Repli si la photo n'est pas encore disponible : portrait illustré en aplats.
function PortraitIllustre() {
  return (
    <svg viewBox="0 0 64 64" className="h-full w-full" aria-hidden="true" xmlns="http://www.w3.org/2000/svg">
      <rect width="64" height="64" fill="#fdf5d9" />
      <path d="M12 64 C12 50 21 44 32 44 C43 44 52 50 52 64 Z" fill="#0f8a63" />
      <rect x="28" y="36" width="8" height="10" rx="3" fill="#7a4a2e" />
      <ellipse cx="32" cy="30" rx="10.5" ry="12" fill="#8a5a3c" />
      <path d="M20 28 C18 12 46 10 44 28 C40 21 24 21 20 28 Z" fill="#e8603c" />
      <ellipse cx="42" cy="15" rx="6" ry="4.5" fill="#f2875f" />
      <circle cx="28" cy="30" r="1.2" fill="#3b2416" />
      <circle cx="36" cy="30" r="1.2" fill="#3b2416" />
      <path d="M28.5 36 Q32 38.5 35.5 36" fill="none" stroke="#3b2416" strokeWidth="1.4" strokeLinecap="round" />
    </svg>
  );
}

function Photo() {
  const [echec, setEchec] = useState(false);
  return (
    <span className="relative block h-16 w-16 shrink-0 overflow-clip rounded-2xl ring-4 ring-soleil-50">
      {echec ? (
        <PortraitIllustre />
      ) : (
        <img src={PHOTO_CLIENTE} alt="" className="h-full w-full scale-125 object-cover object-[50%_35%]" onError={() => setEchec(true)} />
      )}
    </span>
  );
}

export default function CarteScoring() {
  const arc = CIRCONFERENCE * (1 - PD / 100); // le vert couvre la part « sans défaut »
  return (
    <div className="rounded-2xl border border-bord bg-white p-5">
      <div className="flex items-center gap-4">
        <Photo />
        <div className="min-w-0 flex-1">
          <p className="font-display text-lg font-bold leading-tight text-encre">Awa Ndiaye</p>
          <p className="mt-1 flex flex-wrap items-center gap-x-3 gap-y-1 text-sm text-texte-doux">
            <span className="inline-flex items-center gap-1.5">
              <Scissors className="h-3.5 w-3.5 text-terre" aria-hidden="true" />
              Couturière
            </span>
            <span className="inline-flex items-center gap-1.5">
              <MapPin className="h-3.5 w-3.5 text-marque-600" aria-hidden="true" />
              Marché HLM, Dakar
            </span>
          </p>
        </div>
      </div>

      <div className="mt-5 grid items-center gap-5 sm:grid-cols-[auto_1fr]">
        <div className="relative mx-auto h-36 w-36">
          <svg viewBox="0 0 128 128" className="h-full w-full -rotate-90" aria-hidden="true">
            <circle cx="64" cy="64" r={RAYON} fill="none" stroke="#e3f5ee" strokeWidth="12" />
            <circle cx="64" cy="64" r={RAYON} fill="none" stroke="#0f8a63" strokeWidth="12" strokeLinecap="round"
              strokeDasharray={CIRCONFERENCE} strokeDashoffset={CIRCONFERENCE - arc} className="animate-anneau" />
          </svg>
          <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
            <span className="font-display text-3xl font-extrabold leading-none text-encre">8,2 %</span>
            <span className="mt-1 max-w-[6.5rem] text-[0.7rem] leading-tight text-texte-doux">probabilité de défaut</span>
          </div>
        </div>

        <div>
          <span className="inline-flex items-center gap-1.5 rounded-full bg-baobab-50 px-3 py-1 text-sm font-semibold text-baobab">
            <span className="h-2 w-2 rounded-full bg-baobab" aria-hidden="true" />
            Risque faible
          </span>
          <ul className="mt-4 space-y-3">
            {FACTEURS.map(({ icone: Icone, libelle, valeur, ton }, i) => (
              <li key={libelle}>
                <span className="inline-flex items-center gap-1.5 text-xs text-texte-doux">
                  <Icone className="h-3.5 w-3.5" aria-hidden="true" />
                  {libelle}
                </span>
                <div className="mt-1.5 h-2 overflow-clip rounded-full bg-fond">
                  <span className={"block h-full origin-left animate-barre rounded-full " + ton}
                    style={{ width: valeur + "%", animationDelay: 0.4 + i * 0.15 + "s" }} />
                </div>
              </li>
            ))}
          </ul>
        </div>
      </div>

      <div className="mt-5 flex flex-wrap items-center justify-between gap-3 border-t border-bord pt-4">
        <span className="inline-flex items-center gap-2 text-sm text-texte-doux">
          <Sparkles className="h-4 w-4 text-soleil-fonce" aria-hidden="true" />
          Recommandation
        </span>
        <span className="inline-flex animate-apparition items-center gap-2 rounded-full bg-baobab px-4 py-2 text-sm font-semibold text-white shadow-md"
          style={{ animationDelay: "1.2s" }}>
          <BadgeCheck className="h-4 w-4" aria-hidden="true" />
          Prêt accordé
        </span>
      </div>
    </div>
  );
}
