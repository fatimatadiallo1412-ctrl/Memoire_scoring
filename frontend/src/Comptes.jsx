import { useCallback, useEffect, useState } from "react";
import { appeler } from "./api";
import { LIBELLE_ROLE } from "./roles.js";
import Cadre from "./Cadre.jsx";
import {
  Alerte, Badge, Bouton, Champ, Chargement, Liste, MotDePasseTemp, Panneau, TD, TH, Tableau, classeSaisie,
} from "./ui.jsx";

const VIDE = { email: "", nom_complet: "", role: "agent_credit", agence_id: "" };

function dateHeure(iso) {
  if (!iso) return "Jamais";
  const d = new Date(iso);
  return d.toLocaleDateString("fr-FR") + " " + d.toLocaleTimeString("fr-FR", { hour: "2-digit", minute: "2-digit" });
}

export default function Comptes() {
  const [comptes, setComptes] = useState(null);
  const [agences, setAgences] = useState([]);
  const [filtreRole, setFiltreRole] = useState("");
  const [q, setQ] = useState("");
  const [formulaireOuvert, setFormulaireOuvert] = useState(false);
  const [f, setF] = useState(VIDE);
  const [secret, setSecret] = useState(null);
  const [confirmer, setConfirmer] = useState(null);
  const [erreur, setErreur] = useState("");
  const [envoi, setEnvoi] = useState(false);

  const charger = useCallback(async () => {
    try {
      setComptes(await appeler("/comptes", { params: { role: filtreRole, q: q.trim().length >= 2 ? q.trim() : "" } }));
    } catch (e) {
      setErreur(e.message);
    }
  }, [filtreRole, q]);

  useEffect(() => {
    if (q.trim().length === 1) return;
    const minuteur = setTimeout(charger, 300);
    return () => clearTimeout(minuteur);
  }, [charger, q]);

  useEffect(() => {
    appeler("/agences")
      .then((liste) => {
        setAgences(liste);
        if (liste.length > 0) setF((a) => ({ ...a, agence_id: String(liste[0].id) }));
      })
      .catch(() => {});
  }, []);

  async function basculer(compte) {
    setErreur("");
    try {
      await appeler("/comptes/" + compte.id + "/activation", { methode: "PUT", json: { actif: !compte.actif } });
      await charger();
    } catch (e) {
      setErreur(e.message);
    }
  }

  async function reinitialiser(compte) {
    if (confirmer !== compte.id) {
      setConfirmer(compte.id);
      return;
    }
    setErreur("");
    setConfirmer(null);
    try {
      const r = await appeler("/comptes/" + compte.id + "/reinitialiser", { methode: "POST" });
      setSecret({ email: r.email, motDePasse: r.mot_de_passe_temporaire });
    } catch (e) {
      setErreur(e.message);
    }
  }

  async function creer(e) {
    e.preventDefault();
    setErreur("");
    setEnvoi(true);
    try {
      const r = await appeler("/comptes", {
        methode: "POST",
        json: {
          email: f.email.trim(),
          nom_complet: f.nom_complet.trim(),
          role: f.role,
          agence_id: f.role === "agent_credit" ? parseInt(f.agence_id, 10) : null,
        },
      });
      setSecret({ email: r.email, motDePasse: r.mot_de_passe_temporaire });
      setF({ ...VIDE, agence_id: f.agence_id });
      setFormulaireOuvert(false);
      await charger();
    } catch (err) {
      setErreur(err.message);
    } finally {
      setEnvoi(false);
    }
  }

  return (
    <Cadre titre="Comptes utilisateurs"
      actions={<Bouton onClick={() => setFormulaireOuvert(!formulaireOuvert)}>
        {formulaireOuvert ? "Fermer" : "+ Nouveau compte du personnel"}
      </Bouton>}>
      {erreur && <Alerte>{erreur}</Alerte>}
      {secret && <MotDePasseTemp email={secret.email} motDePasse={secret.motDePasse} onFermer={() => setSecret(null)} />}

      {formulaireOuvert && (
        <Panneau titre="Nouveau compte du personnel">
          <form className="grid gap-4 sm:grid-cols-2" onSubmit={creer}>
            <Champ label="Nom complet">
              <input className={classeSaisie} value={f.nom_complet} required minLength={2} maxLength={150}
                onChange={(e) => setF({ ...f, nom_complet: e.target.value })} />
            </Champ>
            <Champ label="E-mail (identifiant de connexion)">
              <input className={classeSaisie} type="email" value={f.email} required
                onChange={(e) => setF({ ...f, email: e.target.value })} />
            </Champ>
            <Champ label="Rôle">
              <Liste valeur={f.role} onChange={(v) => setF({ ...f, role: v })}
                options={[["agent_credit", "Gestionnaire"], ["decideur", "Directeur"]]} />
            </Champ>
            {f.role === "agent_credit" && (
              <Champ label="Agence">
                <Liste valeur={f.agence_id} onChange={(v) => setF({ ...f, agence_id: v })}
                  options={agences.map((a) => [String(a.id), a.nom + " (" + a.zone + ")"])} />
              </Champ>
            )}
            <div className="sm:col-span-2">
              <Bouton type="submit" disabled={envoi}>{envoi ? "Création…" : "Créer le compte"}</Bouton>
              <p className="mt-2 text-xs text-slate-500">
                Un mot de passe temporaire sera généré. Il n'existe qu'un seul administrateur : ce rôle n'est pas proposé.
              </p>
            </div>
          </form>
        </Panneau>
      )}

      <div className="mb-3 grid gap-3 sm:grid-cols-3">
        <input className={classeSaisie + " sm:col-span-2"} type="search" value={q}
          placeholder="Rechercher par nom ou e-mail (2 caractères minimum)" onChange={(e) => setQ(e.target.value)} />
        <select className={classeSaisie} value={filtreRole} onChange={(e) => setFiltreRole(e.target.value)}
          aria-label="Filtrer par rôle">
          <option value="">Tous les rôles</option>
          {Object.entries(LIBELLE_ROLE).map(([cle, libelle]) => <option key={cle} value={cle}>{libelle}</option>)}
        </select>
      </div>

      {!comptes && !erreur && <Chargement />}
      {comptes && (
        <Tableau>
          <thead className="bg-slate-50">
            <tr>
              <th className={TH}>Nom</th>
              <th className={TH + " hidden md:table-cell"}>E-mail</th>
              <th className={TH}>Rôle</th>
              <th className={TH}>État</th>
              <th className={TH + " hidden lg:table-cell"}>Dernière connexion</th>
              <th className={TH}></th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 bg-white">
            {comptes.map((c) => (
              <tr key={c.id}>
                <td className={TD + " font-medium"}>{c.nom_complet}</td>
                <td className={TD + " hidden md:table-cell"}>{c.email}</td>
                <td className={TD}>{LIBELLE_ROLE[c.role] || c.role}</td>
                <td className={TD}>
                  {c.actif ? <Badge ton="vert">Actif</Badge> : <Badge ton="rouge">Désactivé</Badge>}
                  {c.doit_changer_mdp && <span className="ml-1"><Badge ton="orange">Mot de passe temporaire</Badge></span>}
                </td>
                <td className={TD + " hidden lg:table-cell"}>{dateHeure(c.derniere_connexion)}</td>
                <td className={TD + " text-right"}>
                  {c.role === "administrateur" ? (
                    <span className="text-xs text-slate-400">Compte protégé</span>
                  ) : (
                    <div className="flex flex-wrap justify-end gap-2">
                      <Bouton variante="secondaire" onClick={() => basculer(c)}>{c.actif ? "Désactiver" : "Activer"}</Bouton>
                      <Bouton variante={confirmer === c.id ? "danger" : "secondaire"} onClick={() => reinitialiser(c)}>
                        {confirmer === c.id ? "Confirmer ?" : "Réinitialiser le mot de passe"}
                      </Bouton>
                    </div>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </Tableau>
      )}
    </Cadre>
  );
}
