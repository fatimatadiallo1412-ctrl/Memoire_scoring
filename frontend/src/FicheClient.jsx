import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { appeler } from "./api";
import { useAuth } from "./auth.jsx";
import { dateFr } from "./formats.js";
import { LIBELLE_CATEGORIE, LOGEMENTS, SITUATIONS, TYPES_REVENU } from "./listes.js";
import { invaliderMetiers } from "./metiers.js";
import ChampMetier from "./ChampMetier.jsx";
import AssistantPersonnel from "./AssistantPersonnel.jsx";
import Cadre from "./Cadre.jsx";
import { Alerte, Bouton, Case, Champ, Chargement, LienBouton, Liste, Panneau, classeSaisie } from "./ui.jsx";

// Champs d'identité : les modifier n'invalide pas les scores existants.
const IDENTITE = ["nom", "prenom", "telephone", "adresse", "sexe"];
const ENTIERS = ["anciennete_activite_mois", "nb_enfants", "taille_menage", "revenu_mensuel"];
const FACULTATIFS = ["sexe", "telephone", "adresse", "profession"];

function libelleMetier(code, metiers) {
  if (!code) return "";
  const metier = metiers.find((m) => m.code === code);
  return metier ? metier.libelle : code;
}

function versFormulaire(c, metiers) {
  return {
    nom: c.nom,
    prenom: c.prenom,
    date_naissance: c.date_naissance,
    sexe: c.sexe ?? "",
    telephone: c.telephone ?? "",
    adresse: c.adresse ?? "",
    type_revenu: c.type_revenu,
    profession: libelleMetier(c.profession, metiers),
    situation_familiale: c.situation_familiale,
    type_logement: c.type_logement,
    anciennete_activite_mois: String(c.anciennete_activite_mois),
    nb_enfants: String(c.nb_enfants),
    taille_menage: String(c.taille_menage),
    possede_bien_immobilier: c.possede_bien_immobilier,
    possede_vehicule: c.possede_vehicule,
    revenu_mensuel: String(c.revenu_mensuel),
  };
}

function valeurApi(cle, valeur) {
  if (ENTIERS.includes(cle)) return parseInt(valeur, 10);
  if (FACULTATIFS.includes(cle)) {
    const propre = typeof valeur === "string" ? valeur.trim() : valeur;
    return propre === "" ? null : propre;
  }
  return valeur;
}

export default function FicheClient() {
  const { id } = useParams();
  const { utilisateur } = useAuth();
  const peutDemander = ["agent_credit", "administrateur"].includes(utilisateur.role);
  const responsable = ["decideur", "administrateur"].includes(utilisateur.role);
  const [client, setClient] = useState(null);
  const [metiers, setMetiers] = useState([]);
  const [f, setF] = useState(null);
  const [erreur, setErreur] = useState("");
  const [message, setMessage] = useState("");
  const [envoi, setEnvoi] = useState(false);

  useEffect(() => {
    setClient(null);
    setErreur("");
    Promise.all([appeler("/clients/" + id), appeler("/professions")])
      .then(([c, liste]) => {
        setMetiers(liste);
        setClient(c);
        setF(versFormulaire(c, liste));
      })
      .catch((e) => setErreur(e.message));
  }, [id]);

  function changer(cle, valeur) {
    setMessage("");
    setF((ancien) => ({ ...ancien, [cle]: valeur }));
  }

  async function enregistrer(evenement) {
    evenement.preventDefault();
    setErreur("");
    setMessage("");
    const original = versFormulaire(client, metiers);
    const modifies = Object.keys(f).filter((cle) => f[cle] !== original[cle]);
    if (modifies.length === 0) {
      setMessage("Aucune modification à enregistrer.");
      return;
    }
    const corps = Object.fromEntries(modifies.map((cle) => [cle, valeurApi(cle, f[cle])]));
    setEnvoi(true);
    try {
      const maj = await appeler("/clients/" + id, { methode: "PATCH", json: corps });
      const liste = await appeler("/professions");
      invaliderMetiers();
      setMetiers(liste);
      setClient(maj);
      setF(versFormulaire(maj, liste));
      setMessage("Enregistré : " + modifies.join(", ") + ".");
    } catch (e) {
      setErreur(e.message);
    } finally {
      setEnvoi(false);
    }
  }

  if (erreur && !client) {
    return (
      <Cadre titre="Client">
        <Alerte>{erreur}</Alerte>
        <Link className="text-marque-700 underline" to="/clients">Retour à la liste</Link>
      </Cadre>
    );
  }
  if (!client || !f) {
    return (
      <Cadre titre="Client">
        <Chargement />
      </Cadre>
    );
  }

  const marque = (cle) => (IDENTITE.includes(cle) ? "" : " ⚠");
  const aClasser = client.profession && !client.categorie_profession;

  return (
    <Cadre titre={client.prenom + " " + client.nom}
      actions={peutDemander && (
        <LienBouton to={"/demandes/nouvelle?client_id=" + client.id}>+ Nouvelle demande de crédit</LienBouton>
      )}>
      <p className="mb-1 text-sm text-slate-500">
        Code {client.code_client} · gestionnaire n° {client.gestionnaire_id ?? "aucun"} · créé le{" "}
        {dateFr(client.cree_le.slice(0, 10))}
      </p>
      {client.categorie_profession && (
        <p className="mb-3 text-sm text-slate-500">
          Catégorie de métier utilisée par le modèle :{" "}
          {LIBELLE_CATEGORIE[client.categorie_profession] || client.categorie_profession}
        </p>
      )}
      {aClasser && (
        <Alerte ton="attention">
          Le métier « {libelleMetier(client.profession, metiers)} » n'est pas encore classé : tant qu'un
          responsable ne lui a pas attribué une catégorie, le score utilise « Non renseigné ».{" "}
          {responsable
            ? <Link className="underline" to="/metiers">Classer les métiers</Link>
            : "Le directeur ou l'administrateur doit le classer."}
        </Alerte>
      )}
      {message && <Alerte ton="succes">{message}</Alerte>}
      {erreur && <Alerte>{erreur}</Alerte>}

      <Panneau titre="Informations du client">
        <p className="mb-4 text-xs text-slate-500">
          ⚠ : modifier ce champ rend non valides les scores déjà calculés pour ce client ; il faudra recalculer
          le score des dossiers concernés.
        </p>
        <form className="grid gap-4 sm:grid-cols-2" onSubmit={enregistrer}>
          <Champ label="Nom">
            <input className={classeSaisie} value={f.nom} required maxLength={100}
              onChange={(e) => changer("nom", e.target.value)} />
          </Champ>
          <Champ label="Prénom">
            <input className={classeSaisie} value={f.prenom} required maxLength={100}
              onChange={(e) => changer("prenom", e.target.value)} />
          </Champ>
          <Champ label={"Date de naissance" + marque("date_naissance")}>
            <input className={classeSaisie} type="date" value={f.date_naissance} required
              max={new Date().toISOString().slice(0, 10)}
              onChange={(e) => changer("date_naissance", e.target.value)} />
          </Champ>
          <Champ label="Sexe">
            <Liste valeur={f.sexe} onChange={(v) => changer("sexe", v)} facultatif
              options={[["F", "Féminin"], ["M", "Masculin"]]} />
          </Champ>
          <Champ label="Téléphone">
            <input className={classeSaisie} type="tel" value={f.telephone} maxLength={20}
              onChange={(e) => changer("telephone", e.target.value)} />
          </Champ>
          <Champ label="Adresse">
            <input className={classeSaisie} value={f.adresse} maxLength={200}
              onChange={(e) => changer("adresse", e.target.value)} />
          </Champ>
          <Champ label={"Type de revenu" + marque("type_revenu")}>
            <Liste valeur={f.type_revenu} options={TYPES_REVENU} onChange={(v) => changer("type_revenu", v)} />
          </Champ>
          <Champ label={"Profession" + marque("profession")}>
            <ChampMetier valeur={f.profession} onChange={(v) => changer("profession", v)} metiers={metiers} />
          </Champ>
          <Champ label={"Situation familiale" + marque("situation_familiale")}>
            <Liste valeur={f.situation_familiale} options={SITUATIONS}
              onChange={(v) => changer("situation_familiale", v)} />
          </Champ>
          <Champ label={"Logement" + marque("type_logement")}>
            <Liste valeur={f.type_logement} options={LOGEMENTS} onChange={(v) => changer("type_logement", v)} />
          </Champ>
          <Champ label={"Ancienneté de l'activité (mois)" + marque("anciennete_activite_mois")}>
            <input className={classeSaisie} type="number" min="0" value={f.anciennete_activite_mois} required
              onChange={(e) => changer("anciennete_activite_mois", e.target.value)} />
          </Champ>
          <Champ label={"Enfants" + marque("nb_enfants")}>
            <input className={classeSaisie} type="number" min="0" max="30" value={f.nb_enfants} required
              onChange={(e) => changer("nb_enfants", e.target.value)} />
          </Champ>
          <Champ label={"Taille du ménage" + marque("taille_menage")}>
            <input className={classeSaisie} type="number" min="1" max="40" value={f.taille_menage} required
              onChange={(e) => changer("taille_menage", e.target.value)} />
          </Champ>
          <Champ label={"Revenu mensuel moyen estimé (FCFA)" + marque("revenu_mensuel")}>
            <input className={classeSaisie} type="number" min="0" value={f.revenu_mensuel} required
              onChange={(e) => changer("revenu_mensuel", e.target.value)} />
          </Champ>
          <div className="grid gap-2 sm:col-span-2 sm:grid-cols-2">
            <Case libelle={"Possède un bien immobilier" + marque("possede_bien_immobilier")}
              checked={f.possede_bien_immobilier} onChange={(v) => changer("possede_bien_immobilier", v)} />
            <Case libelle={"Possède un véhicule" + marque("possede_vehicule")}
              checked={f.possede_vehicule} onChange={(v) => changer("possede_vehicule", v)} />
          </div>
          <div className="flex flex-wrap items-center gap-3 sm:col-span-2">
            <Bouton type="submit" disabled={envoi}>{envoi ? "Enregistrement…" : "Enregistrer"}</Bouton>
            <Link className="text-sm text-marque-700 underline" to="/clients">Retour à la liste</Link>
          </div>
        </form>
      </Panneau>
      <AssistantPersonnel clientId={client.id} />
    </Cadre>
  );
}
