import { useState } from "react";

// Découpe une liste déjà chargée en pages (aucun appel à l'API).
// Revient à la page 1 quand le nombre d'éléments change (nouveau filtre, nouvelle recherche).
export function usePagination(liste, parPage = 10) {
  const total = liste ? liste.length : 0;
  const [etat, setEtat] = useState({ page: 1, total });
  let page = etat.page;
  if (etat.total !== total) {
    page = 1;
    setEtat({ page: 1, total });
  }
  const nbPages = Math.max(1, Math.ceil(total / parPage));
  if (page > nbPages) page = nbPages;
  const debut = (page - 1) * parPage;
  return {
    page,
    nbPages,
    total,
    debut,
    fin: Math.min(debut + parPage, total),
    elements: liste ? liste.slice(debut, debut + parPage) : liste,
    allerA: (p) => setEtat({ page: Math.min(Math.max(1, p), nbPages), total }),
  };
}
