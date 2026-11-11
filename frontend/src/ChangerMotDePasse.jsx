import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { appeler } from "./api";
import { useAuth } from "./auth.jsx";
import { accueilDe } from "./roles.js";
import Cadre from "./Cadre.jsx";
import LogoMarque from "./LogoMarque.jsx";
import { Alerte, Bouton, Champ, Panneau, classeSaisie } from "./ui.jsx";

export default function ChangerMotDePasse() {
  const { utilisateur, rafraichir, deconnecter } = useAuth();
  const navigate = useNavigate();
  const obligatoire = utilisateur.doit_changer_mdp;
  const [ancien, setAncien] = useState("");
  const [nouveau, setNouveau] = useState("");
  const [confirmation, setConfirmation] = useState("");
  const [erreur, setErreur] = useState("");
  const [succes, setSucces] = useState("");
  const [envoi, setEnvoi] = useState(false);

  async function soumettre(e) {
    e.preventDefault();
    setErreur("");
    setSucces("");
    if (nouveau.length < 8) return setErreur("Le nouveau mot de passe doit contenir au moins 8 caractères.");
    if (nouveau !== confirmation) return setErreur("Les deux saisies du nouveau mot de passe sont différentes.");
    if (nouveau === ancien) return setErreur("Le nouveau mot de passe doit être différent de l'ancien.");
    setEnvoi(true);
    try {
      await appeler("/auth/mot-de-passe", { methode: "POST", json: { ancien, nouveau } });
      const moi = await rafraichir();
      if (obligatoire) {
        navigate(accueilDe(moi), { replace: true });
      } else {
        setSucces("Votre mot de passe a été modifié.");
        setAncien("");
        setNouveau("");
        setConfirmation("");
      }
    } catch (err) {
      setErreur(err.message);
    } finally {
      setEnvoi(false);
    }
  }

  const formulaire = (
    <form onSubmit={soumettre} className="grid gap-4">
      {erreur && <Alerte>{erreur}</Alerte>}
      {succes && <Alerte ton="succes">{succes}</Alerte>}
      <Champ label={obligatoire ? "Mot de passe temporaire reçu" : "Mot de passe actuel"}>
        <input className={classeSaisie} type="password" value={ancien} required autoComplete="current-password"
          onChange={(e) => setAncien(e.target.value)} />
      </Champ>
      <Champ label="Nouveau mot de passe" aide="8 caractères minimum.">
        <input className={classeSaisie} type="password" value={nouveau} required minLength={8}
          autoComplete="new-password" onChange={(e) => setNouveau(e.target.value)} />
      </Champ>
      <Champ label="Confirmer le nouveau mot de passe">
        <input className={classeSaisie} type="password" value={confirmation} required minLength={8}
          autoComplete="new-password" onChange={(e) => setConfirmation(e.target.value)} />
      </Champ>
      <div className="flex flex-wrap items-center gap-3">
        <Bouton type="submit" disabled={envoi}>{envoi ? "Enregistrement…" : "Changer le mot de passe"}</Bouton>
        {obligatoire && (
          <button type="button" className="text-sm text-slate-500 underline" onClick={deconnecter}>Se déconnecter</button>
        )}
      </div>
    </form>
  );

  if (obligatoire) {
    return (
      <div className="relative flex min-h-screen items-center justify-center overflow-clip bg-marque-900 px-4 py-10">
        <div className="pointer-events-none absolute -left-24 -top-24 h-80 w-80 rounded-full bg-marque-800" aria-hidden="true" />
        <div className="pointer-events-none absolute -bottom-20 -right-16 h-64 w-64 rounded-full bg-marque-800" aria-hidden="true" />
        <div className="pointer-events-none absolute bottom-24 left-[15%] h-6 w-6 animate-flotter rounded-full bg-soleil" aria-hidden="true" />
        <div className="relative w-full max-w-md animate-apparition rounded-[2rem] bg-white p-7 shadow-2xl sm:p-10">
        <LogoMarque className="mb-5 h-12 w-12" />
          <h1 className="text-2xl font-extrabold text-encre">Choisissez votre mot de passe</h1>
          <p className="mb-4 mt-1 text-sm text-slate-500">
            Pour la sécurité de votre compte, remplacez le mot de passe temporaire par le vôtre.
          </p>
          {formulaire}
        </div>
      </div>
    );
  }
  return (
    <Cadre titre="Mon mot de passe">
      <Panneau className="max-w-md">{formulaire}</Panneau>
    </Cadre>
  );
}
