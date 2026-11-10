import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { appeler } from "./api";
import { LOGEMENTS, SITUATIONS, TYPES_REVENU } from "./listes.js";
import Cadre from "./Cadre.jsx";
import ChampMetier from "./ChampMetier.jsx";
import { invaliderMetiers } from "./metiers.js";
import { Alerte, Bouton, Case, Champ, Liste, Panneau, classeSaisie } from "./ui.jsx";

const VIDE = {
  nom: "", prenom: "", date_naissance: "", sexe: "", telephone: "", adresse: "",
  agence_id: "", type_revenu: "independant", profession: "",
  situation_familiale: "celibataire", type_logement: "locataire",
  anciennete_activite_mois: "0", nb_enfants: "0", taille_menage: "1",
  possede_bien_immobilier: false, possede_vehicule: false, revenu_mensuel: "0",
};

export default function NouveauClient() {
  const navigate = useNavigate();
  const [f, setF] = useState(VIDE);
  const [agences, setAgences] = useState([]);
  const [erreur, setErreur] = useState("");
  const [envoi, setEnvoi] = useState(false);

  useEffect(() => {
    appeler("/agences")
      .then((liste) => {
        setAgences(liste);
        if (liste.length > 0) setF((a) => ({ ...a, agence_id: String(liste[0].id) }));
      })
      .catch((e) => setErreur(e.message));
  }, []);

  function changer(cle, valeur) {
    setF((a) => ({ ...a, [cle]: valeur }));
  }

  async function creer(evenement) {
    evenement.preventDefault();
    setErreur("");
    setEnvoi(true);
    const corps = {
      nom: f.nom.trim(),
      prenom: f.prenom.trim(),
      date_naissance: f.date_naissance,
      sexe: f.sexe || null,
      telephone: f.telephone || null,
      adresse: f.adresse || null,
      agence_id: parseInt(f.agence_id, 10),
      type_revenu: f.type_revenu,
      profession: f.profession.trim() || null,
      situation_familiale: f.situation_familiale,
      type_logement: f.type_logement,
      anciennete_activite_mois: parseInt(f.anciennete_activite_mois, 10),
      nb_enfants: parseInt(f.nb_enfants, 10),
      taille_menage: parseInt(f.taille_menage, 10),
      possede_bien_immobilier: f.possede_bien_immobilier,
      possede_vehicule: f.possede_vehicule,
      revenu_mensuel: parseInt(f.revenu_mensuel, 10),
    };
    try {
      const client = await appeler("/clients", { methode: "POST", json: corps });
      invaliderMetiers();
      navigate("/clients/" + client.id);
    } catch (e) {
      setErreur(e.message);
      setEnvoi(false);
    }
  }

  return (
    <Cadre titre="Nouveau client">
      {erreur && <Alerte>{erreur}</Alerte>}
      <Panneau>
        <form className="grid gap-4 sm:grid-cols-2" onSubmit={creer}>
          <Champ label="Nom">
            <input className={classeSaisie} value={f.nom} required maxLength={100}
              onChange={(e) => changer("nom", e.target.value)} />
          </Champ>
          <Champ label="Prénom">
            <input className={classeSaisie} value={f.prenom} required maxLength={100}
              onChange={(e) => changer("prenom", e.target.value)} />
          </Champ>
          <Champ label="Date de naissance">
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
          <Champ label="Agence">
            <Liste valeur={f.agence_id} onChange={(v) => changer("agence_id", v)}
              options={agences.map((a) => [String(a.id), a.nom + " (" + a.zone + ")"])} />
          </Champ>
          <Champ label="Type de revenu">
            <Liste valeur={f.type_revenu} options={TYPES_REVENU} onChange={(v) => changer("type_revenu", v)} />
          </Champ>
          <Champ label="Profession">
            <ChampMetier valeur={f.profession} onChange={(v) => changer("profession", v)} />
          </Champ>
          <Champ label="Situation familiale">
            <Liste valeur={f.situation_familiale} options={SITUATIONS}
              onChange={(v) => changer("situation_familiale", v)} />
          </Champ>
          <Champ label="Logement">
            <Liste valeur={f.type_logement} options={LOGEMENTS} onChange={(v) => changer("type_logement", v)} />
          </Champ>
          <Champ label="Ancienneté de l'activité (mois)">
            <input className={classeSaisie} type="number" min="0" value={f.anciennete_activite_mois} required
              onChange={(e) => changer("anciennete_activite_mois", e.target.value)} />
          </Champ>
          <Champ label="Enfants">
            <input className={classeSaisie} type="number" min="0" max="30" value={f.nb_enfants} required
              onChange={(e) => changer("nb_enfants", e.target.value)} />
          </Champ>
          <Champ label="Taille du ménage">
            <input className={classeSaisie} type="number" min="1" max="40" value={f.taille_menage} required
              onChange={(e) => changer("taille_menage", e.target.value)} />
          </Champ>
          <Champ label="Revenu mensuel moyen estimé (FCFA)">
            <input className={classeSaisie} type="number" min="0" value={f.revenu_mensuel} required
              onChange={(e) => changer("revenu_mensuel", e.target.value)} />
          </Champ>
          <div className="grid gap-2 sm:col-span-2 sm:grid-cols-2">
            <Case libelle="Possède un bien immobilier" checked={f.possede_bien_immobilier}
              onChange={(v) => changer("possede_bien_immobilier", v)} />
            <Case libelle="Possède un véhicule" checked={f.possede_vehicule}
              onChange={(v) => changer("possede_vehicule", v)} />
          </div>
          <div className="flex flex-wrap items-center gap-3 sm:col-span-2">
            <Bouton type="submit" disabled={envoi}>{envoi ? "Création…" : "Créer le client"}</Bouton>
            <Link className="text-sm text-marque-700 underline" to="/clients">Annuler</Link>
          </div>
        </form>
      </Panneau>
    </Cadre>
  );
}
