export function dateFr(iso) {
  if (!iso) return "";
  return new Date(iso + "T00:00:00").toLocaleDateString("fr-FR");
}

export function fcfa(montant) {
  return Number(montant).toLocaleString("fr-FR") + " FCFA";
}
