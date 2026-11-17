// Informations propres à la microfinance. Facultatives : elles ne changent pas le score actuel
// (le modèle a appris sur des données qui ne les contiennent pas), mais elles serviront aux
// prochains modèles appris sur les remboursements de l'institution.
export const CHAMPS_MICROFINANCE = ["epargne_mensuelle", "membre_groupement", "usage_mobile_money", "activite_saisonniere"];

const ouiNon = (v) => (v === true ? "oui" : v === false ? "non" : "");

export function microfinanceVersFormulaire(c = {}) {
  return {
    epargne_mensuelle: c.epargne_mensuelle === null || c.epargne_mensuelle === undefined ? "" : String(c.epargne_mensuelle),
    membre_groupement: ouiNon(c.membre_groupement),
    usage_mobile_money: c.usage_mobile_money ?? "",
    activite_saisonniere: ouiNon(c.activite_saisonniere),
  };
}

export function microfinanceVersApi(cle, valeur) {
  if (valeur === "") return null;
  if (cle === "epargne_mensuelle") return parseInt(valeur, 10);
  if (cle === "membre_groupement" || cle === "activite_saisonniere") return valeur === "oui";
  return valeur;
}
