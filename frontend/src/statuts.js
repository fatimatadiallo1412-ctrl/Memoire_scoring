// Couleur du badge de chaque statut de dossier.
const TONS_DOSSIER = {
  brouillon: "neutre", complet: "neutre", score: "bleu", instruit: "bleu", soumis_decision: "orange",
  accorde: "vert", accorde_modifie: "vert", decaisse: "vert", en_remboursement: "vert", solde: "vert",
  refuse: "rouge", ajourne: "orange", contentieux: "rouge",
};

export function tonDossier(statut) {
  return TONS_DOSSIER[statut] || "neutre";
}
