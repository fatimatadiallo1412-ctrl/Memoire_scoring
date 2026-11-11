import { useEffect, useState } from "react";
import { appeler } from "./api";
import { Alerte, Bouton, Champ, MotDePasseTemp, Panneau, classeSaisie } from "./ui.jsx";
import { AIDE_GMAIL, GMAIL } from "./validation.js";

export default function AccesClient({ clientId }) {
  const [email, setEmail] = useState("");
  const [envoi, setEnvoi] = useState(false);
  const [erreur, setErreur] = useState("");
  const [secret, setSecret] = useState(null);

  useEffect(() => {
    setEmail("");
    setErreur("");
    setSecret(null);
  }, [clientId]);

  async function creer(e) {
    e.preventDefault();
    setErreur("");
    setEnvoi(true);
    try {
      const r = await appeler("/comptes/client", { methode: "POST", json: { client_id: clientId, email: email.trim() } });
      setSecret({ email: r.email, motDePasse: r.mot_de_passe_temporaire });
      setEmail("");
    } catch (err) {
      setErreur(err.message);
    } finally {
      setEnvoi(false);
    }
  }

  return (
    <Panneau titre="Accès à l'espace client">
      <p className="mb-3 text-sm text-slate-600">
        Ouvre un compte pour que ce client consulte ses échéances et pose ses questions à l'assistant. Vérifiez son
        identité avant de lui remettre le mot de passe temporaire. S'il a déjà un compte, un message vous le dira.
      </p>
      {erreur && <Alerte>{erreur}</Alerte>}
      {secret && <MotDePasseTemp email={secret.email} motDePasse={secret.motDePasse} onFermer={() => setSecret(null)} />}
      <form className="flex flex-col gap-3 sm:flex-row sm:items-end" onSubmit={creer}>
        <div className="flex-1">
          <Champ label="E-mail du client (identifiant de connexion)" aide={AIDE_GMAIL}>
            <input className={classeSaisie} type="email" value={email} required {...GMAIL} onChange={(e) => setEmail(e.target.value)} />
          </Champ>
        </div>
        <Bouton type="submit" disabled={envoi}>{envoi ? "Création…" : "Créer l'accès"}</Bouton>
      </form>
    </Panneau>
  );
}
