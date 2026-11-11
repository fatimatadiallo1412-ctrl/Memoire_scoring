import { ChevronLeft, ChevronRight } from "lucide-react";

// Numéros à afficher : toujours la première et la dernière page, la page courante et ses voisines.
function numeros(page, nbPages) {
  const garder = new Set([1, nbPages, page - 1, page, page + 1]);
  const liste = [];
  for (let p = 1; p <= nbPages; p++) {
    if (garder.has(p)) liste.push(p);
    else if (liste[liste.length - 1] !== "…") liste.push("…");
  }
  return liste;
}

const FLECHE =
  "inline-flex h-10 min-w-10 items-center justify-center gap-1 rounded-xl bg-white px-2.5 text-sm font-medium text-encre ring-1 ring-inset ring-bord transition duration-200 hover:bg-fond hover:ring-marque-200 active:scale-95 disabled:pointer-events-none disabled:opacity-40";

export default function Pagination({ page, nbPages, total, debut, fin, allerA }) {
  if (nbPages <= 1) return null;
  return (
    <nav aria-label="Pagination" className="mt-4 flex animate-apparition flex-col items-center justify-between gap-3 sm:flex-row">
      <p className="text-sm text-texte-doux" aria-live="polite">
        <span className="font-semibold text-encre">{debut + 1}–{fin}</span> sur {total}
      </p>
      <div className="flex items-center gap-1.5">
        <button type="button" className={FLECHE} onClick={() => allerA(page - 1)} disabled={page === 1}
          aria-label="Page précédente">
          <ChevronLeft className="h-4 w-4" aria-hidden="true" />
          <span className="hidden pr-1 sm:inline">Précédent</span>
        </button>
        {numeros(page, nbPages).map((p, i) =>
          p === "…" ? (
            <span key={"e" + i} className="px-1 text-sm text-texte-doux" aria-hidden="true">…</span>
          ) : (
            <button key={p} type="button" onClick={() => allerA(p)} aria-current={p === page ? "page" : undefined}
              aria-label={"Page " + p}
              className={
                "inline-flex h-10 min-w-10 items-center justify-center rounded-xl px-3 text-sm font-semibold transition duration-200 active:scale-95 " +
                (p === page
                  ? "bg-marque-700 text-white shadow-md"
                  : "bg-transparent text-texte-doux hover:bg-white hover:text-encre hover:ring-1 hover:ring-inset hover:ring-bord")
              }>
              {p}
            </button>
          ),
        )}
        <button type="button" className={FLECHE} onClick={() => allerA(page + 1)} disabled={page === nbPages}
          aria-label="Page suivante">
          <span className="hidden pl-1 sm:inline">Suivant</span>
          <ChevronRight className="h-4 w-4" aria-hidden="true" />
        </button>
      </div>
    </nav>
  );
}
