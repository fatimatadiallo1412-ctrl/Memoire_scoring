// Couleur du badge de chaque statut de dossier.
const TONS_DOSSIER = {
  brouillon: "neutre", complet: "neutre", score: "bleu", instruit: "bleu", soumis_decision: "orange",
  accorde: "vert", accorde_modifie: "vert", decaisse: "vert", en_remboursement: "vert", solde: "vert",
  refuse: "rouge", ajourne: "orange", contentieux: "rouge",
};

export function tonDossier(statut) {
  return TONS_DOSSIER[statut] || "neutre";
}

// Libellé affiché de l'état d'une échéance (valeurs renvoyées par l'API).
const LIBELLES_ECHEANCE = {
  payee: "Payée", en_retard: "En retard", partielle: "Partiellement payée", a_venir: "À venir",
};

export function libelleEcheance(statut) {
  return LIBELLES_ECHEANCE[statut] || String(statut).replace(/_/g, " ");
}
