import { useCallback, useEffect, useState } from "react";
import { appeler } from "./api";
import { LIBELLE_ROLE } from "./roles.js";
import Cadre from "./Cadre.jsx";
import { Alerte, Badge, Bouton, Chargement, MotDePasseTemp, Panneau } from "./ui.jsx";

function dateHeure(iso) {
  const d = new Date(iso);
  return d.toLocaleDateString("fr-FR") + " à " + d.toLocaleTimeString("fr-FR", { hour: "2-digit", minute: "2-digit" });
}

export default function Reinitialisations() {
  const [liste, setListe] = useState(null);
  const [confirmer, setConfirmer] = useState(null);
  const [secret, setSecret] = useState(null);
  const [erreur, setErreur] = useState("");

  const charger = useCallback(async () => {
    try {
      setListe(await appeler("/reinitialisations", { params: { statut: "en_attente" } }));
    } catch (e) {
      setErreur(e.message);
    }
  }, []);

  useEffect(() => {
    charger();
  }, [charger]);

  async function traiter(d) {
    if (confirmer !== d.id) {
      setConfirmer(d.id);
      return;
    }
    setConfirmer(null);
    setErreur("");
    try {
      const r = await appeler("/reinitialisations/" + d.id + "/traiter", { methode: "POST" });
      setSecret({ email: r.email, motDePasse: r.mot_de_passe_temporaire });
      await charger();
    } catch (e) {
      setErreur(e.message);
    }
  }

  async function rejeter(d) {
    setErreur("");
    try {
      await appeler("/reinitialisations/" + d.id + "/rejeter", { methode: "POST" });
      await charger();
    } catch (e) {
      setErreur(e.message);
    }
  }

  return (
    <Cadre titre="Demandes de réinitialisation">
      <Alerte ton="info">
        Avant de générer un mot de passe temporaire, <strong>vérifiez l'identité de la personne</strong> hors de
        l'application (appel, agence). Pour un client, contactez son gestionnaire pour confirmer.
      </Alerte>
      {erreur && <Alerte>{erreur}</Alerte>}
      {secret && <MotDePasseTemp email={secret.email} motDePasse={secret.motDePasse} onFermer={() => setSecret(null)} />}
      {!liste && !erreur && <Chargement />}
      {liste && liste.length === 0 && (
        <Panneau><p className="text-sm text-slate-600">Aucune demande en attente.</p></Panneau>
      )}
      {liste && liste.map((d) => (
        <Panneau key={d.id} titre={d.nom_complet} droite={<Badge ton="orange">En attente</Badge>}>
          <dl className="grid gap-2 text-sm sm:grid-cols-2">
            <div><dt className="text-xs uppercase text-slate-500">E-mail</dt><dd>{d.email}</dd></div>
            <div><dt className="text-xs uppercase text-slate-500">Rôle</dt><dd>{LIBELLE_ROLE[d.role] || d.role}</dd></div>
            {d.gestionnaire && (
              <div><dt className="text-xs uppercase text-slate-500">Gestionnaire du client</dt><dd>{d.gestionnaire}</dd></div>
            )}
            <div><dt className="text-xs uppercase text-slate-500">Téléphone indiqué</dt><dd>{d.contact || "—"}</dd></div>
            <div><dt className="text-xs uppercase text-slate-500">Demandé le</dt><dd>{dateHeure(d.cree_le)}</dd></div>
          </dl>
          <div className="mt-4 flex flex-wrap gap-2">
            <Bouton variante={confirmer === d.id ? "danger" : "primaire"} onClick={() => traiter(d)}>
              {confirmer === d.id ? "Identité vérifiée : confirmer ?" : "Générer un mot de passe temporaire"}
            </Bouton>
            <Bouton variante="secondaire" onClick={() => rejeter(d)}>Rejeter</Bouton>
          </div>
        </Panneau>
      ))}
    </Cadre>
  );
}
