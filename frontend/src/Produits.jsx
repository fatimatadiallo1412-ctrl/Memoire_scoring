import { Link } from "react-router-dom";
import { PRODUITS } from "./vitrine.js";
import Vitrine from "./Vitrine.jsx";

// Cartes interactives (non cliquables) : elles s'agrandissent doucement au survol.
const CARTE =
  "relative flex flex-col rounded-carte border border-bord bg-white p-6 transition duration-200 ease-out hover:z-10 hover:border-marque-600 hover:shadow-md motion-safe:hover:scale-[1.03]";

export default function Produits() {
  return (
    <Vitrine>
      <section className="mx-auto max-w-6xl px-4 py-12">
        <h1 className="text-titre font-bold text-texte">Nos produits</h1>
        <p className="mt-3 max-w-3xl text-slate-600">
          Des crédits pensés pour les activités de nos clients. Le montant et la durée accordés dépendent de
          l'étude de chaque dossier.
        </p>
        <div className="mt-8 grid gap-6 md:grid-cols-2">
          {PRODUITS.map((p) => (
            <article key={p.nom} className={CARTE}>
              <h2 className="text-sous-titre font-semibold text-marque-700">{p.nom}</h2>
              <p className="mt-1 text-sm font-medium text-texte-doux">Pour : {p.pour}</p>
              <p className="mt-3 text-slate-700">{p.description}</p>
              <dl className="mt-4 grid grid-cols-2 gap-3 border-t border-slate-100 pt-4 text-sm">
                <div><dt className="text-xs uppercase tracking-wide text-texte-doux">Montant</dt><dd className="font-medium">{p.montant}</dd></div>
                <div><dt className="text-xs uppercase tracking-wide text-texte-doux">Durée</dt><dd className="font-medium">{p.duree}</dd></div>
              </dl>
            </article>
          ))}
        </div>
        <div className="mt-10 rounded-carte bg-marque-50 p-6">
          <h2 className="text-lg font-semibold text-texte">Comment faire une demande ?</h2>
          <p className="mt-1 text-sm text-slate-700">
            Présentez-vous à votre agence avec une pièce d'identité : votre gestionnaire ouvre votre dossier et vous
            accompagne tout au long de l'étude.
          </p>
          <Link to="/contact" className="mt-3 inline-flex min-h-11 items-center text-sm font-medium text-marque-700 underline">
            Nous contacter
          </Link>
        </div>
      </section>
    </Vitrine>
  );
}
