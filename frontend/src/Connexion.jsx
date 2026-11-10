import { useState } from "react";
import { Bell, CalendarDays, Eye, EyeOff, MessageCircle, TriangleAlert } from "lucide-react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import { useAuth } from "./auth.jsx";
import { MARQUE } from "./marque.js";
import { accueilDe } from "./roles.js";
import { Alerte, Bouton, Champ, classeSaisie } from "./ui.jsx";
import Vitrine from "./Vitrine.jsx";

// Colonne d'information : contenu neutre, sans rien révéler de l'organisation interne.
const AVANTAGES = [
  [CalendarDays, "Vos échéances", "Consultez le calendrier de vos remboursements et ce qu'il reste à payer."],
  [Bell, "Vos rappels", "Retrouvez vos rappels avant chaque échéance."],
  [MessageCircle, "Votre assistant", "Posez vos questions sur votre propre compte."],
];

export default function Connexion() {
  const { utilisateur, connecter } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [motDePasse, setMotDePasse] = useState("");
  const [voir, setVoir] = useState(false);
  const [majuscules, setMajuscules] = useState(false);
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
    <Vitrine>
      <section className="mx-auto grid max-w-6xl items-center gap-10 px-4 py-10 sm:py-16 md:grid-cols-2 md:gap-16">
        <form onSubmit={soumettre}
          className="w-full max-w-md animate-apparition space-y-4 justify-self-center rounded-carte border border-bord bg-white p-6 sm:p-8 md:justify-self-start">
          <div className="text-center">
            <h1 className="text-titre font-semibold text-texte">Connexion</h1>
            <Link to="/" className="mt-1 inline-block text-sm font-medium text-marque-700 underline">{MARQUE.nom}</Link>
          </div>
          {erreur && <Alerte>{erreur}</Alerte>}
          {proposer && (
            <p className="rounded-champ bg-risque-moyen-fond p-3 text-sm text-risque-moyen">
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
            <div className="relative">
              <input className={classeSaisie + " pr-12"} type={voir ? "text" : "password"} value={motDePasse}
                autoComplete="current-password" required
                onChange={(e) => setMotDePasse(e.target.value)}
                onKeyUp={(e) => setMajuscules(e.getModifierState && e.getModifierState("CapsLock"))}
                onBlur={() => setMajuscules(false)} />
              <button type="button" onClick={() => setVoir(!voir)}
                aria-label={voir ? "Masquer le mot de passe" : "Afficher le mot de passe"} aria-pressed={voir}
                className="absolute inset-y-0 right-0 flex w-11 items-center justify-center rounded-champ bg-transparent p-0 text-texte-doux transition-colors duration-150 hover:text-marque-700">
                {voir ? <EyeOff className="h-5 w-5" aria-hidden="true" /> : <Eye className="h-5 w-5" aria-hidden="true" />}
              </button>
            </div>
            {majuscules && (
              <span className="mt-1 flex items-center gap-1.5 text-xs text-risque-moyen">
                <TriangleAlert className="h-3.5 w-3.5" aria-hidden="true" />
                La touche Verr. Maj. est activée.
              </span>
            )}
          </Champ>
          <Bouton type="submit" className="w-full" disabled={envoi}>{envoi ? "Connexion…" : "Se connecter"}</Bouton>
          {!proposer && (
            <p className="text-center text-sm text-slate-500">
              <Link className="underline" to="/mot-de-passe-oublie" state={{ email }}>Mot de passe oublié ?</Link>
            </p>
          )}
        </form>

        <aside className="animate-apparition">
          <h2 className="text-sous-titre font-semibold text-texte">Accédez à votre espace</h2>
          <ul className="mt-5 grid gap-4">
            {AVANTAGES.map(([Icone, titre, texte]) => (
              <li key={titre} className="flex items-start gap-4">
                <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-champ bg-marque-50 text-marque-700">
                  <Icone className="h-5 w-5" aria-hidden="true" />
                </span>
                <div>
                  <p className="font-medium text-texte">{titre}</p>
                  <p className="text-sm text-texte-doux">{texte}</p>
                </div>
              </li>
            ))}
          </ul>
        </aside>
      </section>
    </Vitrine>
  );
}
