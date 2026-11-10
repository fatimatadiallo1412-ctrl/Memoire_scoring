import { useState } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import { MARQUE } from "./marque.js";
import { useAuth } from "./auth.jsx";
import { ACCUEIL } from "./roles.js";
import { Alerte, Bouton, Champ, classeSaisie } from "./ui.jsx";

export default function Connexion() {
  const { utilisateur, connecter } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [motDePasse, setMotDePasse] = useState("");
  const [erreur, setErreur] = useState("");
  const [envoi, setEnvoi] = useState(false);

  if (utilisateur) return <Navigate to={ACCUEIL[utilisateur.role]} replace />;

  async function soumettre(evenement) {
    evenement.preventDefault();
    setErreur("");
    setEnvoi(true);
    try {
      const moi = await connecter(email.trim(), motDePasse);
      navigate(ACCUEIL[moi.role], { replace: true });
    } catch (e) {
      setErreur(e.statut === 401 ? "E-mail ou mot de passe incorrect." : e.message);
    } finally {
      setEnvoi(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-marque-700 to-marque-800 px-4">
      <form onSubmit={soumettre} className="w-full max-w-sm space-y-4 rounded-2xl bg-white p-6 shadow-xl sm:p-8">
        <div className="text-center">
          <h1 className="text-2xl font-semibold text-slate-900">Connexion</h1>
          <Link to="/" className="mt-1 inline-block text-sm font-medium text-marque-700 underline">{MARQUE.nom}</Link>
        </div>
        {erreur && <Alerte>{erreur}</Alerte>}
        <Champ label="E-mail">
          <input className={classeSaisie} type="email" value={email} autoComplete="username" required autoFocus
            onChange={(e) => setEmail(e.target.value)} />
        </Champ>
        <Champ label="Mot de passe">
          <input className={classeSaisie} type="password" value={motDePasse} autoComplete="current-password" required
            onChange={(e) => setMotDePasse(e.target.value)} />
        </Champ>
        <Bouton type="submit" className="w-full" disabled={envoi}>{envoi ? "Connexion…" : "Se connecter"}</Bouton>
      </form>
    </div>
  );
}
