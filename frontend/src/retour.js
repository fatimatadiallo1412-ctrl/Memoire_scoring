// Retour « aperçu » construit à partir du score, avant la décision (personnel seulement).
export function apercuDepuisScore(score) {
  const recours = score && score.facteurs && score.facteurs.recours;
  if (!recours || score.recommandation === "accord") return null;
  return {
    decision: score.recommandation === "accord_reduit" ? "accorder_modifie" : "refuser",
    message: null,
    motifs: recours.motifs.map((m) => m.texte),
    plans: recours.plans,
    institution: recours.institution,
    bloque: recours.bloque,
    calcule: true,
  };
}
