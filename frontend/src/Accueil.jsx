import { Link } from "react-router-dom";
import { MARQUE } from "./marque.js";
import Vitrine from "./Vitrine.jsx";

const ATOUTS = [
  {
    titre: "Une décision éclairée",
    texte: "Un modèle statistique évalue le risque et formule une recommandation. La décision finale reste toujours prise par une personne.",
  },
  {
    titre: "Un accès plus juste au crédit",
    texte: "L'évaluation tient compte du métier, de l'activité et de la situation réelle du client, pas seulement d'un historique bancaire.",
  },
  {
    titre: "Un suivi transparent",
    texte: "Chaque client consulte ses échéances, reçoit des rappels et peut poser ses questions à un assistant sur son propre compte.",
  },
];

const ETAPES = [
  ["Demande", "Le client présente son projet à son gestionnaire en agence."],
  ["Évaluation", "Le dossier est analysé et le modèle calcule un score expliqué."],
  ["Décision", "Le directeur étudie le dossier et décide, avec un commentaire si besoin."],
  ["Suivi", "Après décaissement, échéances, paiements et rappels restent visibles."],
];

export default function Accueil() {
  return (
    <Vitrine>
      <section className="bg-gradient-to-br from-marque-700 to-marque-800 text-white">
        <div className="mx-auto max-w-6xl px-4 py-16 sm:py-24">
          <h1 className="max-w-3xl text-3xl font-bold leading-tight sm:text-5xl">{MARQUE.slogan}</h1>
          <p className="mt-5 max-w-2xl text-lg text-blue-100">
            {MARQUE.nom} met un système de décision au service de la microfinance : évaluer le risque avec méthode,
            expliquer chaque décision et accompagner les clients jusqu'au dernier remboursement.
          </p>
          <div className="mt-8 flex flex-wrap gap-3">
            <Link to="/connexion"
              className="rounded-md bg-white px-5 py-3 text-sm font-semibold text-marque-700 hover:bg-blue-50">
              Se connecter
            </Link>
            <Link to="/produits"
              className="rounded-md px-5 py-3 text-sm font-semibold text-white ring-1 ring-inset ring-white/60 hover:bg-white/10">
              Découvrir nos produits
            </Link>
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-4 py-14">
        <h2 className="text-2xl font-semibold text-slate-900">Ce qui nous distingue</h2>
        <div className="mt-6 grid gap-5 md:grid-cols-3">
          {ATOUTS.map((a) => (
            <article key={a.titre} className="rounded-xl bg-slate-50 p-6 ring-1 ring-slate-200">
              <h3 className="text-lg font-semibold text-marque-700">{a.titre}</h3>
              <p className="mt-2 text-sm text-slate-600">{a.texte}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="bg-marque-50">
        <div className="mx-auto max-w-6xl px-4 py-14">
          <h2 className="text-2xl font-semibold text-slate-900">Notre ambition</h2>
          <p className="mt-3 max-w-3xl text-slate-700">
            Promouvoir l'inclusion financière : permettre aux commerçants, artisans, agriculteurs et salariés à
            revenu modeste d'accéder au crédit sur la base de critères clairs, explicables et appliqués de la même
            façon à tous. Nous voulons que chaque refus puisse être compris et que chaque accord soit suivi avec
            bienveillance.
          </p>
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-4 py-14">
        <h2 className="text-2xl font-semibold text-slate-900">Comment ça marche</h2>
        <ol className="mt-6 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
          {ETAPES.map(([titre, texte], i) => (
            <li key={titre} className="rounded-xl p-5 ring-1 ring-slate-200">
              <span className="flex h-8 w-8 items-center justify-center rounded-full bg-marque-700 text-sm font-semibold text-white">
                {i + 1}
              </span>
              <h3 className="mt-3 font-semibold text-slate-900">{titre}</h3>
              <p className="mt-1 text-sm text-slate-600">{texte}</p>
            </li>
          ))}
        </ol>
      </section>

      <section className="bg-slate-100">
        <div className="mx-auto flex max-w-6xl flex-col items-start justify-between gap-4 px-4 py-10 sm:flex-row sm:items-center">
          <div>
            <h2 className="text-xl font-semibold text-slate-900">Une question sur un crédit ?</h2>
            <p className="text-sm text-slate-600">Notre équipe vous répond en agence ou par message.</p>
          </div>
          <Link to="/contact"
            className="rounded-md bg-marque-700 px-5 py-3 text-sm font-semibold text-white hover:bg-marque-800">
            Contactez-nous
          </Link>
        </div>
      </section>
    </Vitrine>
  );
}
