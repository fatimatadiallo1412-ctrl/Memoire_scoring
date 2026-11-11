import {
  ArrowRight, BadgeCheck, Briefcase, CalendarCheck, Eye, FileText, Gauge, Hammer, Lightbulb, Scale, Store, Wheat,
} from "lucide-react";
import { Link } from "react-router-dom";
import TableauBordDemo from "./TableauBordDemo.jsx";
import { SceneDecision, ScenePirogue, SceneSuivi } from "./IllustrationsHero.jsx";
import { MARQUE } from "./marque.js";
import Revele from "./Revele.jsx";
import Vitrine from "./Vitrine.jsx";

const ATOUTS = [
  {
    titre: "Une décision éclairée",
    texte: "Un modèle statistique évalue le risque et formule une recommandation. La décision finale reste toujours prise par une personne.",
    icone: Lightbulb,
    illustration: SceneDecision,
    tuile: "bg-marque-50 text-marque-700",
  },
  {
    titre: "Un accès plus juste au crédit",
    texte: "L'évaluation tient compte du métier, de l'activité et de la situation réelle du client, pas seulement d'un historique bancaire.",
    icone: Scale,
    illustration: ScenePirogue,
    tuile: "bg-soleil-50 text-soleil-fonce",
  },
  {
    titre: "Un suivi transparent",
    texte: "Chaque client consulte ses échéances, reçoit des rappels et peut poser ses questions à un assistant sur son propre compte.",
    icone: Eye,
    illustration: SceneSuivi,
    tuile: "bg-baobab-50 text-baobab",
  },
];

const ETAPES = [
  ["Demande", "Le client présente son projet à son gestionnaire en agence.", FileText],
  ["Évaluation", "Le dossier est analysé et le modèle calcule un score expliqué.", Gauge],
  ["Décision", "Le directeur étudie le dossier et décide, avec un commentaire si besoin.", BadgeCheck],
  ["Suivi", "Après décaissement, échéances, paiements et rappels restent visibles.", CalendarCheck],
];

// Les publics de l'inclusion financière : commerçants, artisans, agriculteurs, salariés (décoratif).
const PUBLICS = [
  { icone: Store, classe: "bg-soleil-50 text-soleil-fonce" },
  { icone: Hammer, classe: "bg-terre-50 text-terre-fonce" },
  { icone: Wheat, classe: "bg-baobab-50 text-baobab" },
  { icone: Briefcase, classe: "bg-marque-50 text-marque-700" },
];

const BOUTON =
  "group inline-flex min-h-12 items-center justify-center gap-2 rounded-full px-6 text-sm font-semibold transition duration-200 ease-out motion-safe:hover:-translate-y-0.5 ";
const FLECHE = "h-4 w-4 transition-transform duration-200 group-hover:translate-x-0.5";

function TitreSection({ children, clair = false, centre = false }) {
  return (
    <div className={centre ? "text-center" : ""}>
      <span className={"mb-4 inline-block h-1.5 w-10 rounded-full " + (clair ? "bg-soleil" : "bg-terre")} aria-hidden="true" />
      <h2 className={"text-[clamp(1.75rem,1.3rem+1.6vw,2.5rem)] font-bold leading-tight " + (clair ? "text-white" : "text-encre")}>
        {children}
      </h2>
    </div>
  );
}

export default function Accueil() {
  return (
    <Vitrine>
      {/* Hero : message centré, puis une maquette du tableau de bord de l'application */}
      <section className="relative overflow-clip border-b border-bord bg-fond">
        {/* Quadrillage léger, comme le fond d'un tableau de bord */}
        <svg className="pointer-events-none absolute inset-0 h-full w-full" aria-hidden="true" xmlns="http://www.w3.org/2000/svg">
          <defs>
            <pattern id="quadrillage" width="32" height="32" patternUnits="userSpaceOnUse">
              <path d="M32 0 H0 V32" fill="none" stroke="#e3e6ef" strokeWidth="1" />
            </pattern>
          </defs>
          <rect width="100%" height="100%" fill="url(#quadrillage)" />
        </svg>

        <div className="relative mx-auto max-w-7xl px-4 pt-14 sm:px-6 sm:pt-20">
          <div className="mx-auto max-w-3xl animate-apparition text-center">
            <h1 className="text-[clamp(2.25rem,1.4rem+3.4vw,4rem)] font-extrabold leading-[1.05] text-encre">
              Décider en quelques minutes, <span className="text-marque-700">pas à l'intuition.</span>
            </h1>
            <span className="mx-auto mt-6 block h-1.5 w-20 rounded-full bg-soleil" aria-hidden="true" />
            <p className="mx-auto mt-6 max-w-2xl text-lg leading-relaxed text-texte-doux">
              {MARQUE.nom} analyse l'historique, les revenus et le comportement de remboursement de chaque client
              pour vous donner un score clair, explicable, et une recommandation.
            </p>
            <div className="mt-9 flex flex-wrap justify-center gap-3">
              <Link to="/connexion" className={BOUTON + "bg-marque-700 text-white shadow-md hover:bg-marque-800 hover:shadow-lg"}>
                Se connecter
                <ArrowRight className={FLECHE} aria-hidden="true" />
              </Link>
              <Link to="/produits" className={BOUTON + "bg-white text-encre ring-1 ring-inset ring-bord hover:ring-marque-400"}>
                Découvrir nos produits
              </Link>
            </div>
          </div>

          <div className="relative mx-auto mt-14 max-w-5xl animate-apparition pb-16 sm:mt-16 sm:pb-20" style={{ animationDelay: "150ms" }}>
            <div className="absolute inset-x-10 -top-5 bottom-10 rounded-[2rem] bg-marque-100 sm:inset-x-16" aria-hidden="true" />
            <div className="relative">
              <TableauBordDemo />
            </div>
          </div>
        </div>
      </section>

      {/* Atouts */}
      <section className="mx-auto max-w-7xl px-4 py-20 sm:px-6 lg:py-28">
        <Revele>
          <TitreSection>Ce qui nous distingue</TitreSection>
        </Revele>
        <div className="mt-12 grid gap-6 md:grid-cols-3">
          {ATOUTS.map((a, i) => {
            const Icone = a.icone;
            const Illustration = a.illustration;
            return (
              <Revele key={a.titre} delai={i * 120} className="h-full">
                <article className="group flex h-full flex-col overflow-clip rounded-3xl bg-fond ring-1 ring-inset ring-bord transition duration-300 ease-out hover:bg-white hover:shadow-xl motion-safe:hover:-translate-y-1">
                  <div className="flex justify-center px-10 pt-8">
                    <div className="w-full max-w-[15rem] transition-transform duration-500 ease-out motion-safe:group-hover:scale-105">
                      <Illustration />
                    </div>
                  </div>
                  <div className="flex flex-1 flex-col p-7 pt-4">
                    <span className={"flex h-11 w-11 items-center justify-center rounded-xl " + a.tuile}>
                      <Icone className="h-5 w-5" aria-hidden="true" />
                    </span>
                    <h3 className="mt-4 text-xl font-bold text-encre">{a.titre}</h3>
                    <p className="mt-2 text-[0.95rem] leading-relaxed text-texte-doux">{a.texte}</p>
                  </div>
                </article>
              </Revele>
            );
          })}
        </div>
      </section>

      {/* Ambition */}
      <section className="relative overflow-clip bg-marque-900 text-white">
        <div className="pointer-events-none absolute -right-20 -top-28 h-96 w-96 rounded-full bg-marque-800" aria-hidden="true" />
        <div className="pointer-events-none absolute -bottom-16 left-1/3 h-40 w-40 rounded-full bg-marque-800" aria-hidden="true" />
        <div className="relative mx-auto grid max-w-7xl items-center gap-14 px-4 py-20 sm:px-6 lg:grid-cols-[1.4fr_1fr] lg:py-28">
          <Revele>
            <TitreSection clair>Notre ambition</TitreSection>
            <p className="mt-6 max-w-3xl text-[clamp(1.125rem,1rem+0.5vw,1.35rem)] font-medium leading-relaxed text-marque-100">
              Promouvoir l'inclusion financière : permettre aux commerçants, artisans, agriculteurs et salariés à
              revenu modeste d'accéder au crédit sur la base de critères clairs, explicables et appliqués de la même
              façon à tous. Nous voulons que chaque refus puisse être compris et que chaque accord soit suivi avec
              bienveillance.
            </p>
          </Revele>
          <div className="mx-auto grid w-full max-w-[17rem] grid-cols-2 gap-4" aria-hidden="true">
            {PUBLICS.map(({ icone: Icone, classe }, i) => (
              <Revele key={i} delai={i * 100}>
                <span className={"flex aspect-square animate-flotter items-center justify-center rounded-3xl " + classe}
                  style={{ animationDelay: i * 0.7 + "s" }}>
                  <Icone className="h-10 w-10 sm:h-12 sm:w-12" strokeWidth={1.6} />
                </span>
              </Revele>
            ))}
          </div>
        </div>
      </section>

      {/* Étapes */}
      <section className="mx-auto max-w-7xl px-4 py-20 sm:px-6 lg:py-28">
        <Revele>
          <TitreSection>Comment ça marche</TitreSection>
        </Revele>
        <div className="relative mt-12">
          <div className="absolute left-8 right-8 top-7 hidden border-t-2 border-dashed border-marque-200 lg:block" aria-hidden="true" />
          <ol className="relative grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
            {ETAPES.map(([titre, texte, Icone], i) => (
              <Revele as="li" key={titre} delai={i * 140}>
                <div className="group h-full">
                  <div className="flex items-center gap-3">
                    <span className="relative flex h-14 w-14 items-center justify-center rounded-2xl bg-marque-700 text-white ring-8 ring-white transition duration-300 ease-out group-hover:bg-soleil group-hover:text-encre motion-safe:group-hover:-rotate-6">
                      <Icone className="h-6 w-6" aria-hidden="true" />
                    </span>
                    <span className="rounded-full bg-marque-50 px-2.5 py-0.5 font-display text-sm font-bold text-marque-700 ring-4 ring-white">{i + 1}</span>
                  </div>
                  <div className="mt-5">
                    <h3 className="text-lg font-bold text-encre">{titre}</h3>
                    <p className="mt-1.5 text-[0.95rem] leading-relaxed text-texte-doux">{texte}</p>
                  </div>
                </div>
              </Revele>
            ))}
          </ol>
        </div>
      </section>

      {/* Contact */}
      <section className="px-4 pb-20 sm:px-6 lg:pb-28">
        <Revele className="mx-auto max-w-7xl">
          <div className="relative overflow-clip rounded-[2rem] bg-marque-700 px-6 py-12 text-white sm:px-12 lg:py-14">
            <div className="pointer-events-none absolute -right-12 -top-20 h-64 w-64 rounded-full bg-marque-600" aria-hidden="true" />
            <div className="pointer-events-none absolute -bottom-14 right-40 h-28 w-28 rounded-full bg-soleil" aria-hidden="true" />
            <div className="relative flex flex-col items-start justify-between gap-8 md:flex-row md:items-center">
              <div>
                <h2 className="text-[clamp(1.5rem,1.2rem+1.2vw,2.25rem)] font-bold leading-tight">Une question sur un crédit ?</h2>
                <p className="mt-2 text-base text-marque-100">Notre équipe vous répond en agence ou par message.</p>
              </div>
              <Link to="/contact" className={BOUTON + "bg-soleil text-encre shadow-md hover:bg-soleil-clair"}>
                Contactez-nous
                <ArrowRight className={FLECHE} aria-hidden="true" />
              </Link>
            </div>
          </div>
        </Revele>
      </section>
    </Vitrine>
  );
}
