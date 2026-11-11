export function dateFr(iso) {
  if (!iso) return "";
  return new Date(iso + "T00:00:00").toLocaleDateString("fr-FR");
}

export function fcfa(montant) {
  return Number(montant).toLocaleString("fr-FR") + " FCFA";
}

// Date du jour au format AAAA-MM-JJ (champs de date) et année en cours.
export function aujourdhuiIso() {
  return new Date().toISOString().slice(0, 10);
}

export function anneeCourante() {
  return new Date().getFullYear();
}
