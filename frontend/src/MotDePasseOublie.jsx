import { useState } from "react";
import { useLocation } from "react-router-dom";
import { appeler } from "./api";
import { MARQUE } from "./marque.js";
import LogoMarque from "./LogoMarque.jsx";
import { Alerte, Bouton, Champ, LienRetour, classeSaisie } from "./ui.jsx";
import { AIDE_TELEPHONE, TELEPHONE } from "./validation.js";

export default function MotDePasseOublie() {
  const lieu = useLocation();
  const [email, setEmail] = useState((lieu.state && lieu.state.email) || "");
  const [contact, setContact] = useState("");
  const [envoi, setEnvoi] = useState(false);
  const [erreur, setErreur] = useState("");
  const [reponse, setReponse] = useState("");

  async function soumettre(e) {
    e.preventDefault();
    setErreur("");
    setEnvoi(true);
    try {
      const r = await appeler("/reinitialisations", {
        methode: "POST",
        json: { email: email.trim(), contact: contact.trim() || null },
      });
      setReponse(r.message);
    } catch (err) {
      setErreur(err.message);
    } finally {
      setEnvoi(false);
    }
  }

  return (
    <div className="relative flex min-h-screen items-center justify-center overflow-clip bg-marque-900 px-4 py-10">
        <div className="pointer-events-none absolute -left-24 -top-24 h-80 w-80 rounded-full bg-marque-800" aria-hidden="true" />
        <div className="pointer-events-none absolute -bottom-20 -right-16 h-64 w-64 rounded-full bg-marque-800" aria-hidden="true" />
        <div className="pointer-events-none absolute bottom-24 left-[15%] h-6 w-6 animate-flotter rounded-full bg-soleil" aria-hidden="true" />
      <div className="relative w-full max-w-md animate-apparition rounded-[2rem] bg-white p-7 shadow-2xl sm:p-10">
        <LogoMarque className="mb-5 h-12 w-12" />
        <h1 className="text-2xl font-extrabold text-encre">Mot de passe oublié</h1>
        {reponse ? (
          <div className="mt-4 space-y-4">
            <Alerte ton="succes">{reponse}</Alerte>
            <div><LienRetour to="/connexion">Retour à la connexion</LienRetour></div>
          </div>
        ) : (
          <form onSubmit={soumettre} className="mt-4 grid gap-4">
            <p className="text-sm text-slate-500">
              Indiquez l'e-mail de votre compte. L'administrateur vérifiera votre identité avant de vous remettre un
              mot de passe temporaire.
            </p>
            {erreur && <Alerte>{erreur}</Alerte>}
            <Champ label="E-mail du compte">
              <input className={classeSaisie} type="email" value={email} required onChange={(e) => setEmail(e.target.value)} />
            </Champ>
            <Champ label="Téléphone pour vous joindre (facultatif)" aide={AIDE_TELEPHONE}>
              <input className={classeSaisie} type="tel" value={contact} maxLength={100} {...TELEPHONE}
                onChange={(e) => setContact(e.target.value)} />
            </Champ>
            <Bouton type="submit" disabled={envoi}>{envoi ? "Envoi…" : "Envoyer la demande"}</Bouton>
            <LienRetour to="/connexion">Retour à la connexion</LienRetour>
          </form>
        )}
        <p className="mt-4 text-center text-xs text-slate-400">{MARQUE.nom}</p>
      </div>
    </div>
  );
}
