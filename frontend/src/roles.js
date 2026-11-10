export const ACCUEIL = {
  agent_credit: "/clients",
  decideur: "/dossiers",
  administrateur: "/comptes",
  client: "/espace",
};

export const LIBELLE_ROLE = {
  agent_credit: "Gestionnaire",
  decideur: "Directeur",
  administrateur: "Administrateur",
  client: "Client",
};

// Un compte au mot de passe temporaire doit d'abord choisir le sien.
export function accueilDe(utilisateur) {
  return utilisateur.doit_changer_mdp ? "/changer-mot-de-passe" : ACCUEIL[utilisateur.role];
}
