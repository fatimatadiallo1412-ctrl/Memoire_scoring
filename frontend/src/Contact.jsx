import { useState } from "react";
import { Clock, Mail, MapPin, Phone, Send, ShieldCheck } from "lucide-react";
import { useLocation } from "react-router-dom";
import { appeler } from "./api";
import { MARQUE } from "./marque.js";
import Revele from "./Revele.jsx";
import Vitrine from "./Vitrine.jsx";
import { Alerte, Bouton, Champ, classeSaisie } from "./ui.jsx";
import { AIDE_GMAIL, GMAIL } from "./validation.js";

const VIDE = { nom: "", email: "", objet: "", message: "", site_web: "" };

export default function Contact() {
  const lieu = useLocation();
  const [f, setF] = useState({ ...VIDE, objet: (lieu.state && lieu.state.objet) || "" });
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

  const coordonnees = [
    [MapPin, "Adresse", MARQUE.adresse],
    [Phone, "Téléphone", MARQUE.telephone],
    [Mail, "E-mail", MARQUE.email],
    [Clock, "Horaires", MARQUE.horaires],
  ];

  return (
    <Vitrine>
      <section className="relative overflow-clip bg-fond">
        <div className="pointer-events-none absolute -left-24 -top-24 h-72 w-72 rounded-full bg-marque-50" aria-hidden="true" />
        <div className="relative mx-auto grid max-w-7xl gap-10 px-4 py-14 sm:px-6 sm:py-20 lg:grid-cols-[1fr_1.15fr] lg:gap-16">
          <div className="animate-apparition">
            <span className="mb-4 block h-1.5 w-10 rounded-full bg-terre" aria-hidden="true" />
            <h1 className="text-[clamp(2.25rem,1.5rem+3vw,3.5rem)] font-extrabold leading-tight text-encre">Contactez-nous</h1>
            <p className="mt-5 max-w-md text-lg leading-relaxed text-texte-doux">
              Une question sur nos produits ou sur votre dossier ? Écrivez-nous ou passez en agence.
            </p>
            <dl className="mt-8 grid gap-3 sm:grid-cols-2 lg:grid-cols-1 xl:grid-cols-2">
              {coordonnees.map(([Icone, libelle, valeur], i) => (
                <Revele key={libelle} delai={i * 90}>
                  <div className="group flex h-full items-start gap-3.5 rounded-2xl bg-white p-4 ring-1 ring-inset ring-bord transition duration-300 hover:shadow-lg motion-safe:hover:-translate-y-0.5">
                    <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-marque-50 text-marque-700 transition-colors duration-300 group-hover:bg-marque-700 group-hover:text-white">
                      <Icone className="h-5 w-5" aria-hidden="true" />
                    </span>
                    <div>
                      <dt className="text-sm font-semibold text-encre">{libelle}</dt>
                      <dd className="mt-0.5 text-sm text-texte-doux">{valeur}</dd>
                    </div>
                  </div>
                </Revele>
              ))}
            </dl>
          </div>

          <form onSubmit={envoyer}
            className="relative grid animate-apparition gap-4 self-start rounded-[2rem] bg-white p-6 shadow-xl ring-1 ring-bord sm:p-9">
            <span className="absolute -right-3 -top-3 flex h-14 w-14 animate-flotter items-center justify-center rounded-2xl bg-soleil text-encre shadow-lg" aria-hidden="true">
              <Send className="h-6 w-6" />
            </span>
            {succes && <Alerte ton="succes">{succes} Nous vous répondrons à l'adresse indiquée.</Alerte>}
            {erreur && <Alerte>{erreur}</Alerte>}
            <div className="grid gap-4 sm:grid-cols-2">
              <Champ label="Nom">
                <input className={classeSaisie} value={f.nom} required minLength={2} maxLength={100}
                  onChange={(e) => setF({ ...f, nom: e.target.value })} />
              </Champ>
              <Champ label="Votre e-mail" aide={AIDE_GMAIL}>
                <input className={classeSaisie} type="email" value={f.email} required {...GMAIL}
                  onChange={(e) => setF({ ...f, email: e.target.value })} />
              </Champ>
            </div>
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
            <p className="flex items-start gap-2 text-xs text-texte-doux">
              <ShieldCheck className="mt-0.5 h-4 w-4 shrink-0 text-baobab" aria-hidden="true" />
              Vos informations servent uniquement à vous répondre. Nous n'enregistrons pas votre adresse IP.
            </p>
            <div><Bouton type="submit" className="w-full sm:w-auto" disabled={envoi}>{envoi ? "Envoi…" : "Envoyer le message"}</Bouton></div>
          </form>
        </div>
      </section>
    </Vitrine>
  );
}
