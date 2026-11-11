import { ArrowRight, Clock, Coins, Hammer, Sofa, Store, Wheat } from "lucide-react";
import { Link } from "react-router-dom";
import { SceneChamp, SceneCouture, SceneMarche, SceneTransfert } from "./IllustrationsHero.jsx";
import Revele from "./Revele.jsx";
import { PRODUITS } from "./vitrine.js";
import Vitrine from "./Vitrine.jsx";

// Habillage visuel de chaque produit, dans l'ordre de PRODUITS (repli sur le premier si la liste s'allonge).
const HABILLAGES = [
  { icone: Store, scene: SceneMarche, fond: "bg-soleil-50", tuile: "bg-soleil text-encre" },
  { icone: Hammer, scene: SceneCouture, fond: "bg-marque-50", tuile: "bg-marque-700 text-white" },
  { icone: Wheat, scene: SceneChamp, fond: "bg-baobab-50", tuile: "bg-baobab text-white" },
  { icone: Sofa, scene: SceneTransfert, fond: "bg-terre-50", tuile: "bg-terre text-white" },
];

export default function Produits() {
  return (
    <Vitrine>
      <section className="relative overflow-clip bg-fond">
        <div className="pointer-events-none absolute -right-24 -top-24 h-72 w-72 rounded-full bg-marque-50" aria-hidden="true" />
        <div className="relative mx-auto max-w-7xl px-4 pb-16 pt-14 sm:px-6 sm:pt-20">
          <div className="max-w-3xl animate-apparition">
            <span className="mb-4 block h-1.5 w-10 rounded-full bg-terre" aria-hidden="true" />
            <h1 className="text-[clamp(2.25rem,1.5rem+3vw,3.5rem)] font-extrabold leading-tight text-encre">Nos produits</h1>
            <p className="mt-5 text-lg leading-relaxed text-texte-doux">
              Des crédits pensés pour les activités de nos clients. Le montant et la durée accordés dépendent de
              l'étude de chaque dossier.
            </p>
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-7xl px-4 py-16 sm:px-6 lg:py-20">
        <div className="grid gap-6 md:grid-cols-2">
          {PRODUITS.map((p, i) => {
            const h = HABILLAGES[i] || HABILLAGES[0];
            const Icone = h.icone;
            const Scene = h.scene;
            return (
              <Revele key={p.nom} delai={(i % 2) * 120} className="h-full">
                <article className="group flex h-full flex-col overflow-clip rounded-3xl bg-white ring-1 ring-inset ring-bord transition duration-300 ease-out hover:shadow-xl motion-safe:hover:-translate-y-1 sm:flex-row">
                  <div className={"flex shrink-0 items-center justify-center p-6 sm:w-48 " + h.fond} aria-hidden="true">
                    <div className="w-36 transition-transform duration-500 ease-out motion-safe:group-hover:scale-110 sm:w-full">
                      <Scene />
                    </div>
                  </div>
                  <div className="flex flex-1 flex-col p-6 sm:p-7">
                    <div className="flex items-center gap-3">
                      <span className={"flex h-10 w-10 shrink-0 items-center justify-center rounded-xl " + h.tuile}>
                        <Icone className="h-5 w-5" aria-hidden="true" />
                      </span>
                      <h2 className="text-xl font-bold text-encre">{p.nom}</h2>
                    </div>
                    <p className="mt-3 text-sm font-medium text-marque-700">Pour : {p.pour}</p>
                    <p className="mt-2 leading-relaxed text-texte-doux">{p.description}</p>
                    <dl className="mt-auto grid grid-cols-1 gap-3 pt-5 text-sm sm:grid-cols-2">
                      <div className="flex items-start gap-2.5 rounded-xl bg-fond p-3">
                        <Coins className="mt-0.5 h-4 w-4 shrink-0 text-marque-600" aria-hidden="true" />
                        <div>
                          <dt className="text-xs font-medium text-texte-doux">Montant</dt>
                          <dd className="font-semibold text-encre">{p.montant}</dd>
                        </div>
                      </div>
                      <div className="flex items-start gap-2.5 rounded-xl bg-fond p-3">
                        <Clock className="mt-0.5 h-4 w-4 shrink-0 text-marque-600" aria-hidden="true" />
                        <div>
                          <dt className="text-xs font-medium text-texte-doux">Durée</dt>
                          <dd className="font-semibold text-encre">{p.duree}</dd>
                        </div>
                      </div>
                    </dl>
                  </div>
                </article>
              </Revele>
            );
          })}
        </div>

        <Revele className="mt-14">
          <div className="relative overflow-clip rounded-[2rem] bg-marque-900 p-8 text-white sm:p-12">
            <div className="pointer-events-none absolute -right-16 -top-16 h-56 w-56 rounded-full bg-marque-800" aria-hidden="true" />
            <div className="pointer-events-none absolute -bottom-10 right-1/4 h-20 w-20 rounded-full bg-soleil" aria-hidden="true" />
            <div className="relative max-w-2xl">
              <h2 className="text-[clamp(1.5rem,1.2rem+1vw,2rem)] font-bold">Comment faire une demande ?</h2>
              <p className="mt-3 leading-relaxed text-marque-100">
                Présentez-vous à votre agence avec une pièce d'identité : votre gestionnaire ouvre votre dossier et vous
                accompagne tout au long de l'étude.
              </p>
              <Link to="/contact"
                className="group mt-7 inline-flex min-h-12 items-center gap-2 rounded-full bg-soleil px-6 text-sm font-semibold text-encre transition duration-200 hover:bg-soleil-clair motion-safe:hover:-translate-y-0.5">
                Nous contacter
                <ArrowRight className="h-4 w-4 transition-transform duration-200 group-hover:translate-x-0.5" aria-hidden="true" />
              </Link>
            </div>
          </div>
        </Revele>
      </section>
    </Vitrine>
  );
}
