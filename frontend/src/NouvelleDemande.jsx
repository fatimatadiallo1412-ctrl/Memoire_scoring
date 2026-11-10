import { useEffect, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { appeler } from "./api";
import { fcfa } from "./formats.js";
import Cadre from "./Cadre.jsx";
import { Alerte, Bouton, Champ, Panneau, classeSaisie } from "./ui.jsx";

export default function NouvelleDemande() {
  const [params] = useSearchParams();
  const clientId = params.get("client_id");
  const navigate = useNavigate();
  const [client, setClient] = useState(null);
  const [produits, setProduits] = useState([]);
  const [produitId, setProduitId] = useState("");
  const [montant, setMontant] = useState("");
  const [duree, setDuree] = useState("");
  const [objet, setObjet] = useState("");
  const [erreur, setErreur] = useState("");
  const [envoi, setEnvoi] = useState(false);

  useEffect(() => {
    if (!clientId) {
      setErreur("Aucun client choisi : ouvrez d'abord la fiche d'un client.");
      return;
    }
    appeler("/clients/" + clientId).then(setClient).catch((e) => setErreur(e.message));
    appeler("/produits")
      .then((liste) => {
        setProduits(liste);
        if (liste.length > 0) setProduitId(String(liste[0].id));
      })
      .catch((e) => setErreur(e.message));
  }, [clientId]);

  const produit = produits.find((p) => String(p.id) === produitId);

  async function creer(evenement) {
    evenement.preventDefault();
    setErreur("");
    setEnvoi(true);
    try {
      const demande = await appeler("/demandes", {
        methode: "POST",
        json: {
          client_id: parseInt(clientId, 10),
          produit_id: parseInt(produitId, 10),
          montant_demande: parseInt(montant, 10),
          duree_mois: parseInt(duree, 10),
          objet: objet.trim() || null,
        },
      });
      navigate("/dossiers/" + demande.id);
    } catch (e) {
      setErreur(e.message);
      setEnvoi(false);
    }
  }

  return (
    <Cadre titre="Nouvelle demande de crédit">
      {erreur && <Alerte>{erreur}</Alerte>}
      <Panneau>
        {client && (
          <p className="mb-4 text-sm text-slate-600">
            Client : <strong className="text-slate-900">{client.prenom} {client.nom}</strong> ({client.code_client})
          </p>
        )}
        <form className="grid gap-4 sm:grid-cols-2" onSubmit={creer}>
          <div className="sm:col-span-2">
            <Champ label="Produit">
              <select className={classeSaisie} value={produitId} required
                onChange={(e) => setProduitId(e.target.value)}>
                {produits.map((p) => (
                  <option key={p.id} value={p.id}>{p.libelle}</option>
                ))}
              </select>
            </Champ>
          </div>
          <Champ label="Montant demandé (FCFA)"
            aide={produit ? "De " + fcfa(produit.montant_min) + " à " + fcfa(produit.montant_max) : undefined}>
            <input className={classeSaisie} type="number" value={montant} required
              min={produit ? produit.montant_min : 1} max={produit ? produit.montant_max : undefined}
              onChange={(e) => setMontant(e.target.value)} />
          </Champ>
          <Champ label="Durée (mois)"
            aide={produit ? "De " + produit.duree_min_mois + " à " + produit.duree_max_mois + " mois" : undefined}>
            <input className={classeSaisie} type="number" value={duree} required
              min={produit ? produit.duree_min_mois : 1} max={produit ? produit.duree_max_mois : 120}
              onChange={(e) => setDuree(e.target.value)} />
          </Champ>
          <div className="sm:col-span-2">
            <Champ label="Objet du crédit (facultatif)">
              <input className={classeSaisie} value={objet} maxLength={200}
                onChange={(e) => setObjet(e.target.value)} />
            </Champ>
          </div>
          <div className="flex flex-wrap items-center gap-3 sm:col-span-2">
            <Bouton type="submit" disabled={envoi || !client}>{envoi ? "Création…" : "Créer la demande"}</Bouton>
            {clientId && <Link className="text-sm text-marque-700 underline" to={"/clients/" + clientId}>Annuler</Link>}
          </div>
        </form>
      </Panneau>
    </Cadre>
  );
}
