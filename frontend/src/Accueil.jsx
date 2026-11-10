import { Eye, Lightbulb, Scale, Sprout } from "lucide-react";
import { Link } from "react-router-dom";
import Carrousel from "./Carrousel.jsx";
import { MARQUE } from "./marque.js";
import Vitrine from "./Vitrine.jsx";

const ATOUTS = [
  {
    titre: "Une décision éclairée",
    texte: "Un modèle statistique évalue le risque et formule une recommandation. La décision finale reste toujours prise par une personne.",
    icone: Lightbulb,
  },
  {
    titre: "Un accès plus juste au crédit",
    texte: "L'évaluation tient compte du métier, de l'activité et de la situation réelle du client, pas seulement d'un historique bancaire.",
    icone: Scale,
  },
  {
    titre: "Un suivi transparent",
    texte: "Chaque client consulte ses échéances, reçoit des rappels et peut poser ses questions à un assistant sur son propre compte.",
    icone: Eye,
  },
];

const ETAPES = [
  ["Demande", "Le client présente son projet à son gestionnaire en agence."],
  ["Évaluation", "Le dossier est analysé et le modèle calcule un score expliqué."],
  ["Décision", "Le directeur étudie le dossier et décide, avec un commentaire si besoin."],
  ["Suivi", "Après décaissement, échéances, paiements et rappels restent visibles."],
];

const DIAPOSITIVES = [
  {
    titre: MARQUE.slogan,
    texte:
      MARQUE.nom +
      " met un système de décision au service de la microfinance : évaluer le risque avec méthode, expliquer chaque décision et accompagner les clients jusqu'au dernier remboursement.",
    icone: Sprout,
  },
  ...ATOUTS,
];

// Cartes interactives (non cliquables) : elles s'agrandissent doucement au survol.
const CARTE =
  "relative rounded-carte border border-bord p-6 transition duration-200 ease-out hover:z-10 hover:border-marque-600 hover:shadow-md motion-safe:hover:scale-[1.04]";

export default function Accueil() {
  return (
    <Vitrine>
      <section className="bg-marque-800 text-white">
        <div className="mx-auto max-w-6xl px-4 py-14 sm:py-20">
          <Carrousel
            diapositives={DIAPOSITIVES}
            actions={
              <>
                <Link to="/connexion"
                  className="inline-flex min-h-12 items-center rounded-champ bg-white px-5 text-sm font-semibold text-marque-700 transition-colors duration-150 hover:bg-marque-50">
                  Se connecter
                </Link>
                <Link to="/produits"
                  className="inline-flex min-h-12 items-center rounded-champ px-5 text-sm font-semibold text-white ring-1 ring-inset ring-white/60 transition-colors duration-150 hover:bg-white/10">
                  Découvrir nos produits
                </Link>
              </>
            }
          />
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-4 py-14">
        <h2 className="text-titre font-semibold text-texte">Ce qui nous distingue</h2>
        <div className="mt-6 grid gap-5 md:grid-cols-3">
          {ATOUTS.map((a) => {
            const Icone = a.icone;
            return (
              <article key={a.titre} className={CARTE + " bg-fond"}>
                <Icone className="h-7 w-7 text-marque-700" aria-hidden="true" />
                <h3 className="mt-3 text-lg font-semibold text-marque-700">{a.titre}</h3>
                <p className="mt-2 text-sm text-slate-600">{a.texte}</p>
              </article>
            );
          })}
        </div>
      </section>

      <section className="bg-marque-50">
        <div className="mx-auto max-w-6xl px-4 py-14">
          <h2 className="text-titre font-semibold text-texte">Notre ambition</h2>
          <p className="mt-3 max-w-3xl text-slate-700">
            Promouvoir l'inclusion financière : permettre aux commerçants, artisans, agriculteurs et salariés à
            revenu modeste d'accéder au crédit sur la base de critères clairs, explicables et appliqués de la même
            façon à tous. Nous voulons que chaque refus puisse être compris et que chaque accord soit suivi avec
            bienveillance.
          </p>
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-4 py-14">
        <h2 className="text-titre font-semibold text-texte">Comment ça marche</h2>
        <ol className="mt-6 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
          {ETAPES.map(([titre, texte], i) => (
            <li key={titre} className={CARTE + " bg-white p-5"}>
              <span className="flex h-8 w-8 items-center justify-center rounded-full bg-marque-700 text-sm font-semibold text-white">
                {i + 1}
              </span>
              <h3 className="mt-3 font-semibold text-slate-900">{titre}</h3>
              <p className="mt-1 text-sm text-slate-600">{texte}</p>
            </li>
          ))}
        </ol>
      </section>

      <section className="bg-fond">
        <div className="mx-auto flex max-w-6xl flex-col items-start justify-between gap-4 px-4 py-10 sm:flex-row sm:items-center">
          <div>
            <h2 className="text-xl font-semibold text-slate-900">Une question sur un crédit ?</h2>
            <p className="text-sm text-slate-600">Notre équipe vous répond en agence ou par message.</p>
          </div>
          <Link to="/contact"
            className="inline-flex min-h-12 items-center rounded-champ bg-marque-700 px-5 text-sm font-semibold text-white transition-colors duration-150 hover:bg-marque-800">
            Contactez-nous
          </Link>
        </div>
      </section>
    </Vitrine>
  );
}
