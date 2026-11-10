import { useState } from "react";
import { appeler } from "./api";
import { MARQUE } from "./marque.js";
import Vitrine from "./Vitrine.jsx";
import { Alerte, Bouton, Champ, classeSaisie } from "./ui.jsx";

const VIDE = { nom: "", email: "", objet: "", message: "", site_web: "" };

export default function Contact() {
  const [f, setF] = useState(VIDE);
  const [envoi, setEnvoi] = useState(false);
  const [erreur, setErreur] = useState("");
  const [succes, setSucces] = useState("");

  async function envoyer(e) {
    e.preventDefault();
    setErreur("");
    setSucces("");
    setEnvoi(true);
    try {
      const reponse = await appeler("/contact", {
        methode: "POST",
        json: {
          nom: f.nom.trim(),
          email: f.email.trim(),
          objet: f.objet.trim() || null,
          message: f.message.trim(),
          site_web: f.site_web,
        },
      });
      setSucces(reponse.message);
      setF(VIDE);
    } catch (err) {
      setErreur(err.message);
    } finally {
      setEnvoi(false);
    }
  }

  return (
    <Vitrine>
      <section className="mx-auto grid max-w-6xl gap-10 px-4 py-12 md:grid-cols-2">
        <div>
          <h1 className="text-3xl font-bold text-slate-900">Contactez-nous</h1>
          <p className="mt-3 text-slate-600">
            Une question sur nos produits ou sur votre dossier ? Écrivez-nous ou passez en agence.
          </p>
          <dl className="mt-6 space-y-4 text-sm">
            <div><dt className="font-semibold text-slate-900">Adresse</dt><dd className="text-slate-600">{MARQUE.adresse}</dd></div>
            <div><dt className="font-semibold text-slate-900">Téléphone</dt><dd className="text-slate-600">{MARQUE.telephone}</dd></div>
            <div><dt className="font-semibold text-slate-900">E-mail</dt><dd className="text-slate-600">{MARQUE.email}</dd></div>
            <div><dt className="font-semibold text-slate-900">Horaires</dt><dd className="text-slate-600">{MARQUE.horaires}</dd></div>
          </dl>
        </div>

        <form onSubmit={envoyer} className="grid gap-4 rounded-xl bg-slate-50 p-6 ring-1 ring-slate-200">
          {succes && <Alerte ton="succes">{succes} Nous vous répondrons à l'adresse indiquée.</Alerte>}
          {erreur && <Alerte>{erreur}</Alerte>}
          <Champ label="Nom">
            <input className={classeSaisie} value={f.nom} required minLength={2} maxLength={100}
              onChange={(e) => setF({ ...f, nom: e.target.value })} />
          </Champ>
          <Champ label="Votre e-mail">
            <input className={classeSaisie} type="email" value={f.email} required
              onChange={(e) => setF({ ...f, email: e.target.value })} />
          </Champ>
          <Champ label="Objet (facultatif)">
            <input className={classeSaisie} value={f.objet} maxLength={150}
              onChange={(e) => setF({ ...f, objet: e.target.value })} />
          </Champ>
          <Champ label="Message" aide="10 caractères minimum.">
            <textarea className={classeSaisie} rows={5} value={f.message} required minLength={10} maxLength={2000}
              onChange={(e) => setF({ ...f, message: e.target.value })} />
          </Champ>
          {/* Piège anti-robots : invisible pour les personnes, rempli par les robots. */}
          <div className="absolute -left-[9999px]" aria-hidden="true">
            <label>Ne pas remplir
              <input tabIndex={-1} autoComplete="off" value={f.site_web}
                onChange={(e) => setF({ ...f, site_web: e.target.value })} />
            </label>
          </div>
          <p className="text-xs text-slate-500">
            Vos informations servent uniquement à vous répondre. Nous n'enregistrons pas votre adresse IP.
          </p>
          <div><Bouton type="submit" disabled={envoi}>{envoi ? "Envoi…" : "Envoyer le message"}</Bouton></div>
        </form>
      </section>
    </Vitrine>
  );
}
