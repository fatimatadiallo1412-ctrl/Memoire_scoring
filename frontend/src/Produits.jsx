import { Link } from "react-router-dom";
import { PRODUITS } from "./vitrine.js";
import Vitrine from "./Vitrine.jsx";

export default function Produits() {
  return (
    <Vitrine>
      <section className="mx-auto max-w-6xl px-4 py-12">
        <h1 className="text-3xl font-bold text-slate-900">Nos produits</h1>
        <p className="mt-3 max-w-3xl text-slate-600">
          Des crédits pensés pour les activités de nos clients. Le montant et la durée accordés dépendent de
          l'étude de chaque dossier.
        </p>
        <div className="mt-8 grid gap-6 md:grid-cols-2">
          {PRODUITS.map((p) => (
            <article key={p.nom} className="flex flex-col rounded-xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
              <h2 className="text-xl font-semibold text-marque-700">{p.nom}</h2>
              <p className="mt-1 text-sm font-medium text-slate-500">Pour : {p.pour}</p>
              <p className="mt-3 text-slate-700">{p.description}</p>
              <dl className="mt-4 grid grid-cols-2 gap-3 border-t border-slate-100 pt-4 text-sm">
                <div><dt className="text-xs uppercase tracking-wide text-slate-500">Montant</dt><dd className="font-medium">{p.montant}</dd></div>
                <div><dt className="text-xs uppercase tracking-wide text-slate-500">Durée</dt><dd className="font-medium">{p.duree}</dd></div>
              </dl>
            </article>
          ))}
        </div>
        <div className="mt-10 rounded-xl bg-marque-50 p-6">
          <h2 className="text-lg font-semibold text-slate-900">Comment faire une demande ?</h2>
          <p className="mt-1 text-sm text-slate-700">
            Présentez-vous à votre agence avec une pièce d'identité : votre gestionnaire ouvre votre dossier et vous
            accompagne tout au long de l'étude.
          </p>
          <Link to="/contact" className="mt-3 inline-block text-sm font-medium text-marque-700 underline">
            Nous contacter
          </Link>
        </div>
      </section>
    </Vitrine>
  );
}
