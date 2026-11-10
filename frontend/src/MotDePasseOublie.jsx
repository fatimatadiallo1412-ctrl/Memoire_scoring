import { useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { appeler } from "./api";
import { MARQUE } from "./marque.js";
import { Alerte, Bouton, Champ, classeSaisie } from "./ui.jsx";

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
    <div className="flex min-h-screen items-center justify-center bg-marque-800 px-4">
      <div className="w-full max-w-sm animate-apparition rounded-carte bg-white p-6 sm:p-8">
        <h1 className="text-sous-titre font-semibold text-texte">Mot de passe oublié</h1>
        {reponse ? (
          <div className="mt-4 space-y-4">
            <Alerte ton="succes">{reponse}</Alerte>
            <Link className="text-sm text-marque-700 underline" to="/connexion">Retour à la connexion</Link>
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
            <Champ label="Téléphone pour vous joindre (facultatif)">
              <input className={classeSaisie} type="tel" value={contact} maxLength={100}
                onChange={(e) => setContact(e.target.value)} />
            </Champ>
            <Bouton type="submit" disabled={envoi}>{envoi ? "Envoi…" : "Envoyer la demande"}</Bouton>
            <Link className="text-center text-sm text-slate-500 underline" to="/connexion">Retour à la connexion</Link>
          </form>
        )}
        <p className="mt-4 text-center text-xs text-slate-400">{MARQUE.nom}</p>
      </div>
    </div>
  );
}
