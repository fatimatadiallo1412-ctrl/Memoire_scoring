import { createContext, useCallback, useContext, useEffect, useState } from "react";
import { appeler, ecrireJeton, lireJeton } from "./api";

const Contexte = createContext(null);

export function useAuth() {
  return useContext(Contexte);
}

export function AuthProvider({ children }) {
  const [utilisateur, setUtilisateur] = useState(null);
  const [chargement, setChargement] = useState(Boolean(lireJeton()));

  const deconnecter = useCallback(() => {
    ecrireJeton(null);
    setUtilisateur(null);
  }, []);

  useEffect(() => {
    if (!lireJeton()) return;
    appeler("/auth/me")
      .then(setUtilisateur)
      .catch(() => ecrireJeton(null))
      .finally(() => setChargement(false));
  }, []);

  useEffect(() => {
    window.addEventListener("session-expiree", deconnecter);
    return () => window.removeEventListener("session-expiree", deconnecter);
  }, [deconnecter]);

  async function connecter(email, motDePasse) {
    const jeton = await appeler("/auth/login", {
      methode: "POST",
      formulaire: { username: email, password: motDePasse },
    });
    ecrireJeton(jeton.access_token);
    const moi = await appeler("/auth/me");
    setUtilisateur(moi);
    return moi;
  }

  return (
    <Contexte.Provider value={{ utilisateur, chargement, connecter, deconnecter }}>
      {children}
    </Contexte.Provider>
  );
}
