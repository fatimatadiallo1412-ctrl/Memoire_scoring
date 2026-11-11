import { createContext, useContext } from "react";

// Contexte de connexion, fourni par AuthProvider (auth.jsx).
export const Contexte = createContext(null);

export function useAuth() {
  return useContext(Contexte);
}
