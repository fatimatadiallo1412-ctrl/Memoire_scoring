const BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";
const CLE_JETON = "jeton";

export function lireJeton() {
  try { return sessionStorage.getItem(CLE_JETON); } catch { return null; }
}

export function ecrireJeton(jeton) {
  try {
    if (jeton) sessionStorage.setItem(CLE_JETON, jeton);
    else sessionStorage.removeItem(CLE_JETON);
  } catch { /* stockage indisponible : on continue sans */ }
}

export class ErreurApi extends Error {
  constructor(statut, message) {
    super(message);
    this.statut = statut;
  }
}

function texteErreur(detail, statut) {
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail.map((d) => (d.loc || []).slice(1).join(".") + " : " + String(d.msg).replace(/^Value error, /, "")).join(" ; ");
  }
  return "Erreur " + statut;
}

export async function appeler(chemin, options = {}) {
  const { methode = "GET", json, formulaire, params } = options;
  const url = new URL(BASE + chemin);
  if (params) {
    for (const [cle, valeur] of Object.entries(params)) {
      if (valeur !== undefined && valeur !== null && valeur !== "") url.searchParams.set(cle, valeur);
    }
  }
  const entetes = {};
  const jeton = lireJeton();
  if (jeton) entetes.Authorization = "Bearer " + jeton;

  let corps;
  if (json !== undefined) {
    entetes["Content-Type"] = "application/json";
    corps = JSON.stringify(json);
  } else if (formulaire) {
    corps = new URLSearchParams(formulaire);
  }

  let reponse;
  try {
    reponse = await fetch(url, { method: methode, headers: entetes, body: corps });
  } catch {
    throw new ErreurApi(0, "Impossible de joindre le serveur.");
  }

  if (reponse.status === 401 && chemin !== "/auth/login") {
    ecrireJeton(null);
    window.dispatchEvent(new Event("session-expiree"));
  }

  let donnees = null;
  if ((reponse.headers.get("content-type") || "").includes("application/json")) {
    donnees = await reponse.json();
  }
  if (!reponse.ok) {
    throw new ErreurApi(reponse.status, texteErreur(donnees && donnees.detail, reponse.status));
  }
  return donnees;
}


// Téléchargement d'un fichier (rapports) : renvoie le contenu et le nom proposé par le serveur.
export async function telecharger(chemin, params = {}) {
  const url = new URL(BASE + chemin);
  Object.entries(params).forEach(([cle, valeur]) => {
    if (valeur !== undefined && valeur !== "") url.searchParams.set(cle, valeur);
  });
  const jeton = lireJeton();
  const reponse = await fetch(url, { headers: jeton ? { Authorization: "Bearer " + jeton } : {} });
  if (!reponse.ok) {
    let detail = "Téléchargement impossible (erreur " + reponse.status + ").";
    try {
      const corps = await reponse.json();
      if (typeof corps.detail === "string") detail = corps.detail;
    } catch {
      // réponse sans JSON : on garde le message par défaut
    }
    throw new Error(detail);
  }
  const entete = reponse.headers.get("Content-Disposition") || "";
  const trouve = entete.match(/filename="?([^";]+)"?/);
  return { blob: await reponse.blob(), nom: trouve ? trouve[1] : "rapport" };
}
