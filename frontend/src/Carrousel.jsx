import { useEffect, useState } from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";

// Carrousel accessible : défilement automatique mis en pause au survol et au focus,
// désactivé si l'utilisateur préfère réduire les animations.
export default function Carrousel({ diapositives, actions, intervalle = 6000 }) {
  const [courante, setCourante] = useState(0);
  const [pause, setPause] = useState(false);
  const [reduit] = useState(() => window.matchMedia("(prefers-reduced-motion: reduce)").matches);
  const n = diapositives.length;

  useEffect(() => {
    if (pause || reduit || n < 2) return undefined;
    const minuteur = setInterval(() => setCourante((i) => (i + 1) % n), intervalle);
    return () => clearInterval(minuteur);
  }, [pause, reduit, n, intervalle]);

  const aller = (i) => setCourante((i + n) % n);

  return (
    <div
      role="region"
      aria-roledescription="carrousel"
      aria-label="Présentation"
      onMouseEnter={() => setPause(true)}
      onMouseLeave={() => setPause(false)}
      onFocus={() => setPause(true)}
      onBlur={() => setPause(false)}
    >
      <div className="overflow-clip">
        <div
          className="flex transition-transform duration-700 ease-[cubic-bezier(0.22,1,0.36,1)]"
          style={{ transform: "translateX(-" + courante * 100 + "%)" }}
          aria-live={pause ? "polite" : "off"}
        >
          {diapositives.map((d, k) => {
            const Icone = d.icone;
            const Illustration = d.illustration;
            const Titre = k === 0 ? "h1" : "h2";
            const active = k === courante;
            return (
              <div
                key={d.titre}
                role="group"
                aria-roledescription="diapositive"
                aria-label={k + 1 + " sur " + n}
                aria-hidden={k !== courante}
                className="flex w-full shrink-0 flex-col items-center justify-between gap-8 md:flex-row md:gap-10"
              >
                <div className={"max-w-2xl transition duration-700 ease-out md:flex-1 " +
                  (active ? "translate-y-0 opacity-100" : "translate-y-3 opacity-0")}>
                  <span className="mb-5 block h-1.5 w-14 rounded-full bg-soleil" aria-hidden="true" />
                  <Titre className="text-[clamp(1.75rem,1.2rem+2.6vw,2.9rem)] font-bold leading-tight tracking-tight">{d.titre}</Titre>
                  <p className="mt-5 text-lg leading-relaxed text-marque-100">{d.texte}</p>
                </div>
                {Illustration ? (
                  <div className={"w-full max-w-[17rem] shrink-0 transition duration-700 ease-out sm:max-w-[21rem] lg:max-w-[27rem] " +
                    (active ? "scale-100 opacity-100" : "scale-95 opacity-0")}>
                    <Illustration />
                  </div>
                ) : (
                  <Icone className="hidden h-44 w-44 shrink-0 text-white/15 md:block" strokeWidth={1.25} aria-hidden="true" />
                )}
              </div>
            );
          })}
        </div>
      </div>

      {actions && <div className="mt-8 flex flex-wrap gap-3">{actions}</div>}

      <div className="mt-6 flex items-center gap-3">
        <button type="button" aria-label="Diapositive précédente" onClick={() => aller(courante - 1)}
          className="flex h-11 w-11 items-center justify-center rounded-full bg-transparent p-0 text-white ring-1 ring-inset ring-white/40 transition-colors duration-150 hover:bg-white/10 hover:ring-soleil">
          <ChevronLeft className="h-6 w-6" aria-hidden="true" />
        </button>
        <div className="flex items-center">
          {diapositives.map((d, k) => (
            <button key={d.titre} type="button" aria-label={"Aller à la diapositive " + (k + 1)}
              aria-current={k === courante} onClick={() => aller(k)}
              className="flex h-11 w-7 items-center justify-center bg-transparent p-0">
              <span className={"block h-2.5 rounded-full transition-all duration-200 " +
                (k === courante ? "w-7 bg-soleil" : "w-2.5 bg-white/40 hover:bg-white/70")} />
            </button>
          ))}
        </div>
        <button type="button" aria-label="Diapositive suivante" onClick={() => aller(courante + 1)}
          className="flex h-11 w-11 items-center justify-center rounded-full bg-transparent p-0 text-white ring-1 ring-inset ring-white/40 transition-colors duration-150 hover:bg-white/10 hover:ring-soleil">
          <ChevronRight className="h-6 w-6" aria-hidden="true" />
        </button>
      </div>
    </div>
  );
}
