import { useState } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import { useAuth } from "./auth.jsx";
import { MARQUE } from "./marque.js";
import { accueilDe } from "./roles.js";
import { Alerte, Bouton, Champ, classeSaisie } from "./ui.jsx";

export default function Connexion() {
  const { utilisateur, connecter } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [motDePasse, setMotDePasse] = useState("");
  const [erreur, setErreur] = useState("");
  const [envoi, setEnvoi] = useState(false);
  const [echecs, setEchecs] = useState(0);
  const [bloque, setBloque] = useState(false);

  if (utilisateur) return <Navigate to={accueilDe(utilisateur)} replace />;

  async function soumettre(evenement) {
    evenement.preventDefault();
    setErreur("");
    setEnvoi(true);
    try {
      const moi = await connecter(email.trim(), motDePasse);
      navigate(accueilDe(moi), { replace: true });
    } catch (e) {
      if (e.statut === 401) {
        setEchecs((n) => n + 1);
        setErreur("E-mail ou mot de passe incorrect. Veuillez réessayer.");
      } else {
        if (e.statut === 429) setBloque(true);
        setErreur(e.message);
      }
    } finally {
      setEnvoi(false);
    }
  }

  const proposer = echecs >= 3 || bloque;

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-marque-700 to-marque-800 px-4">
      <form onSubmit={soumettre} className="w-full max-w-sm space-y-4 rounded-2xl bg-white p-6 shadow-xl sm:p-8">
        <div className="text-center">
          <h1 className="text-2xl font-semibold text-slate-900">Connexion</h1>
          <Link to="/" className="mt-1 inline-block text-sm font-medium text-marque-700 underline">{MARQUE.nom}</Link>
        </div>
        {erreur && <Alerte>{erreur}</Alerte>}
        {proposer && (
          <p className="rounded-md bg-amber-50 p-3 text-sm text-amber-900">
            Vous avez oublié votre mot de passe ?{" "}
            <Link className="font-medium underline" to="/mot-de-passe-oublie" state={{ email }}>
              Demander une réinitialisation
            </Link>
          </p>
        )}
        <Champ label="E-mail">
          <input className={classeSaisie} type="email" value={email} autoComplete="username" required autoFocus
            onChange={(e) => setEmail(e.target.value)} />
        </Champ>
        <Champ label="Mot de passe">
          <input className={classeSaisie} type="password" value={motDePasse} autoComplete="current-password" required
            onChange={(e) => setMotDePasse(e.target.value)} />
        </Champ>
        <Bouton type="submit" className="w-full" disabled={envoi}>{envoi ? "Connexion…" : "Se connecter"}</Bouton>
        {!proposer && (
          <p className="text-center text-sm text-slate-500">
            <Link className="underline" to="/mot-de-passe-oublie" state={{ email }}>Mot de passe oublié ?</Link>
          </p>
        )}
      </form>
    </div>
  );
}
