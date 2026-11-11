import { useCallback, useEffect, useState } from "react";
import { KeyRound, Power, Search, ShieldCheck, UserCheck, UserPlus, UserX, X } from "lucide-react";
import { appeler } from "./api";
import { LIBELLE_ROLE } from "./roles.js";
import Cadre from "./Cadre.jsx";
import Pagination from "./Pagination.jsx";
import { usePagination } from "./usePagination.js";
import {
  Alerte, Avatar, Badge, Bouton, Champ, Chargement, Liste, MotDePasseTemp, Panneau, Statistique, TD, TH, Tableau, classeSaisie,
} from "./ui.jsx";
import { AIDE_GMAIL, GMAIL } from "./validation.js";

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
  const pageComptes = usePagination(comptes, 10);

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
      actions={<Bouton className="gap-2" onClick={() => setFormulaireOuvert(!formulaireOuvert)}>
        {formulaireOuvert ? <X className="h-4 w-4" aria-hidden="true" /> : <UserPlus className="h-4 w-4" aria-hidden="true" />}
        {formulaireOuvert ? "Fermer" : "+ Nouveau compte du personnel"}
      </Bouton>}>
      {erreur && <Alerte>{erreur}</Alerte>}
      {secret && <MotDePasseTemp email={secret.email} motDePasse={secret.motDePasse} onFermer={() => setSecret(null)} />}

      {comptes && (
        <div className="mb-6 grid gap-4 sm:grid-cols-3">
          <Statistique icone={UserCheck} valeur={comptes.filter((c) => c.actif).length} libelle="Actif"
            ton="bg-baobab-50 text-baobab" />
          <Statistique icone={UserX} valeur={comptes.filter((c) => !c.actif).length} libelle="Désactivé"
            ton="bg-terre-50 text-terre-fonce" />
          <Statistique icone={KeyRound} valeur={comptes.filter((c) => c.doit_changer_mdp).length}
            libelle="Mot de passe temporaire" ton="bg-soleil-50 text-soleil-fonce" />
        </div>
      )}

      {formulaireOuvert && (
        <Panneau className="border-marque-200 ring-4 ring-marque-50" titre={
          <span className="flex items-center gap-3">
            <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-marque-700 text-white">
              <UserPlus className="h-5 w-5" aria-hidden="true" />
            </span>
            Nouveau compte du personnel
          </span>
        }>
          <form className="grid gap-4 sm:grid-cols-2" onSubmit={creer}>
            <Champ label="Nom complet">
              <input className={classeSaisie} value={f.nom_complet} required minLength={2} maxLength={150}
                onChange={(e) => setF({ ...f, nom_complet: e.target.value })} />
            </Champ>
            <Champ label="E-mail (identifiant de connexion)" aide={AIDE_GMAIL}>
              <input className={classeSaisie} type="email" value={f.email} required {...GMAIL}
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

      <div className="mb-4 grid gap-3 rounded-carte border border-bord bg-white p-3 sm:grid-cols-3">
        <div className="relative sm:col-span-2">
          <Search className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-texte-doux" aria-hidden="true" />
          <input className={classeSaisie + " pl-10"} type="search" value={q}
            placeholder="Rechercher par nom ou e-mail (2 caractères minimum)" onChange={(e) => setQ(e.target.value)} />
        </div>
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
          <tbody key={pageComptes.page} className="animate-apparition divide-y divide-slate-100 bg-white">
            {pageComptes.elements.map((c) => (
              <tr key={c.id}>
                <td className={TD}>
                  <div className="flex items-center gap-3">
                    <Avatar nom={c.nom_complet} />
                    <div className="min-w-0">
                      <p className="font-semibold text-encre">{c.nom_complet}</p>
                      <p className="truncate text-xs text-texte-doux md:hidden">{c.email}</p>
                    </div>
                  </div>
                </td>
                <td className={TD + " hidden text-texte-doux md:table-cell"}>{c.email}</td>
                <td className={TD}><Badge ton="bleu">{LIBELLE_ROLE[c.role] || c.role}</Badge></td>
                <td className={TD}>
                  {c.actif ? <Badge ton="vert">Actif</Badge> : <Badge ton="rouge">Désactivé</Badge>}
                  {c.doit_changer_mdp && <span className="ml-1 inline-block"><Badge ton="orange">Mot de passe temporaire</Badge></span>}
                </td>
                <td className={TD + " hidden text-texte-doux lg:table-cell"}>{dateHeure(c.derniere_connexion)}</td>
                <td className={TD + " text-right"}>
                  {c.role === "administrateur" ? (
                    <span className="inline-flex items-center gap-1.5 rounded-full bg-fond px-3 py-1 text-xs font-medium text-texte-doux">
                      <ShieldCheck className="h-3.5 w-3.5 text-baobab" aria-hidden="true" />
                      Compte protégé
                    </span>
                  ) : (
                    <div className="flex flex-wrap justify-end gap-2">
                      <Bouton variante="secondaire" className="gap-1.5 !min-h-9" onClick={() => basculer(c)}>
                        <Power className={"h-4 w-4 " + (c.actif ? "text-terre" : "text-baobab")} aria-hidden="true" />
                        {c.actif ? "Désactiver" : "Activer"}
                      </Bouton>
                      <Bouton variante={confirmer === c.id ? "danger" : "secondaire"} className="gap-1.5 !min-h-9" onClick={() => reinitialiser(c)}>
                        <KeyRound className="h-4 w-4" aria-hidden="true" />
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
      {comptes && <Pagination {...pageComptes} />}
    </Cadre>
  );
}
