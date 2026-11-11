import { useCallback, useEffect, useRef, useState } from "react";
import {
  Activity, Clock, Filter, Maximize2, RefreshCw, Scale, ShieldAlert, ShieldCheck, Users,
} from "lucide-react";
import { appeler } from "./api";
import Cadre from "./Cadre.jsx";
import { Alerte, Bouton } from "./ui.jsx";

// Les quatre onglets du tableau Metabase, pour que le directeur sache où chercher.
const RUBRIQUES = [
  { icone: Activity, titre: "Activité", texte: "Demandes, taux d'accord, montants décaissés, délais et charge des gestionnaires.",
    ton: "bg-marque-50 text-marque-700" },
  { icone: ShieldAlert, titre: "Risque", texte: "PAR 30 et PAR 90 face à la norme BCEAO, recouvrement et plus gros impayés.",
    ton: "bg-risque-eleve-fond text-risque-eleve" },
  { icone: Scale, titre: "Aide à la décision", texte: "Suivi des recommandations du modèle et retards observés selon le risque prévu.",
    ton: "bg-soleil-50 text-soleil-fonce" },
  { icone: Users, titre: "Inclusion", texte: "Taux d'accord par sexe, âge, revenu et type d'activité.",
    ton: "bg-baobab-50 text-baobab" },
];

function minutes(secondes) {
  const s = Math.max(0, secondes);
  return Math.floor(s / 60) + " min " + String(s % 60).padStart(2, "0") + " s";
}

export default function TableauBord() {
  const [lien, setLien] = useState(null);
  const [erreur, setErreur] = useState("");
  const [charge, setCharge] = useState(false);
  const [expireA, setExpireA] = useState(0);
  const [reste, setReste] = useState(0);
  const cadre = useRef(null);

  const charger = useCallback(async () => {
    setErreur("");
    setLien(null);
    setCharge(false);
    try {
      const r = await appeler("/tableau-de-bord/lien");
      setLien(r.url);
      setExpireA(Date.now() + r.expire_dans_secondes * 1000);
      setReste(r.expire_dans_secondes);
    } catch (e) {
      setErreur(e.message);
    }
  }, []);

  useEffect(() => {
    charger();
  }, [charger]);

  // Compte à rebours de validité du lien signé.
  useEffect(() => {
    if (!expireA) return undefined;
    const minuteur = setInterval(() => setReste(Math.round((expireA - Date.now()) / 1000)), 1000);
    return () => clearInterval(minuteur);
  }, [expireA]);

  const expire = lien && reste <= 0;
  const bientot = lien && reste > 0 && reste <= 60;

  function pleinEcran() {
    cadre.current?.requestFullscreen?.();
  }

  return (
    <Cadre titre="Tableau de bord">
      <p className="mb-6 max-w-3xl text-texte-doux">
        Le pilotage de l'activité de crédit en un coup d'œil. Filtrez par période, agence ou produit en haut du tableau ;
        le survol du titre d'un graphique affiche sa définition.
      </p>

      <div className="mb-6 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        {RUBRIQUES.map(({ icone: Icone, titre, texte, ton }, i) => (
          <div key={titre} style={{ animationDelay: i * 60 + "ms" }}
            className="flex animate-apparition gap-3 rounded-carte border border-bord bg-white p-4">
            <span className={"flex h-10 w-10 shrink-0 items-center justify-center rounded-xl " + ton}>
              <Icone className="h-5 w-5" aria-hidden="true" />
            </span>
            <div>
              <p className="font-semibold text-encre">{titre}</p>
              <p className="mt-0.5 text-sm leading-snug text-texte-doux">{texte}</p>
            </div>
          </div>
        ))}
      </div>

      {erreur && (
        <div className="mb-6">
          <Alerte>{erreur}</Alerte>
          <Bouton variante="secondaire" onClick={charger} className="mt-3 gap-2">
            <RefreshCw className="h-4 w-4" aria-hidden="true" /> Réessayer
          </Bouton>
        </div>
      )}

      {!erreur && (
        <section ref={cadre} className="overflow-hidden rounded-carte border border-bord bg-white shadow-[0_1px_2px_rgba(18,24,40,0.04)]">
          <div className="flex flex-wrap items-center justify-between gap-3 border-b border-bord px-4 py-3 sm:px-5">
            <div className="flex flex-wrap items-center gap-3">
              <h2 className="font-bold text-encre">Tableau de bord du directeur</h2>
              {lien && !expire && (
                <span className={"inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium " +
                  (bientot ? "bg-risque-moyen-fond text-risque-moyen" : "bg-risque-faible-fond text-risque-faible")}>
                  <Clock className="h-3.5 w-3.5" aria-hidden="true" />
                  Accès valable encore {minutes(reste)}
                </span>
              )}
              <span className="hidden items-center gap-1.5 text-xs text-texte-doux md:inline-flex">
                <Filter className="h-3.5 w-3.5" aria-hidden="true" /> Filtres : période, agence, produit
              </span>
            </div>
            <div className="flex gap-2">
              <Bouton variante="secondaire" onClick={charger} className="gap-2" aria-label="Actualiser le tableau de bord">
                <RefreshCw className="h-4 w-4" aria-hidden="true" /> <span className="hidden sm:inline">Actualiser</span>
              </Bouton>
              <Bouton variante="secondaire" onClick={pleinEcran} disabled={!lien} className="gap-2" aria-label="Afficher en plein écran">
                <Maximize2 className="h-4 w-4" aria-hidden="true" /> <span className="hidden sm:inline">Plein écran</span>
              </Bouton>
            </div>
          </div>

          <div className="relative h-[78vh] min-h-[560px] bg-fond">
            {lien && (
              <iframe src={lien} title="Tableau de bord" onLoad={() => setCharge(true)}
                className={"h-full w-full bg-white transition-opacity duration-500 " + (charge ? "opacity-100" : "opacity-0")} />
            )}

            {!charge && !expire && (
              <div className="absolute inset-0 grid gap-4 p-5 sm:grid-cols-4" aria-hidden="true">
                {[0, 1, 2, 3].map((i) => <div key={i} className="h-24 animate-pulse rounded-xl bg-bord/70" />)}
                <div className="h-64 animate-pulse rounded-xl bg-bord/70 sm:col-span-2" />
                <div className="h-64 animate-pulse rounded-xl bg-bord/70 sm:col-span-2" />
              </div>
            )}

            {expire && (
              <div className="absolute inset-0 flex items-center justify-center bg-encre/40 p-4 backdrop-blur-[2px]">
                <div className="max-w-sm animate-apparition rounded-carte bg-white p-6 text-center shadow-xl">
                  <span className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-marque-50 text-marque-700">
                    <Clock className="h-6 w-6" aria-hidden="true" />
                  </span>
                  <p className="mt-3 font-semibold text-encre">L'accès au tableau de bord a expiré</p>
                  <p className="mt-1 text-sm text-texte-doux">Pour votre sécurité, le lien n'est valable que 10 minutes.</p>
                  <Bouton onClick={charger} className="mt-4 gap-2">
                    <RefreshCw className="h-4 w-4" aria-hidden="true" /> Renouveler l'accès
                  </Bouton>
                </div>
              </div>
            )}
          </div>
        </section>
      )}

      <p className="mt-4 flex items-start gap-2 text-xs text-texte-doux">
        <ShieldCheck className="mt-0.5 h-4 w-4 shrink-0 text-baobab" aria-hidden="true" />
        L'accès est personnel et temporaire : il expire après 10 minutes (cliquez sur « Actualiser » pour le renouveler)
        et chaque ouverture est inscrite au journal d'audit.
      </p>
    </Cadre>
  );
}
