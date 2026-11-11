import { useCallback, useEffect, useState } from "react";
import { Clock, KeyRound, Mail, Phone, ShieldCheck, UserCog, Users, X } from "lucide-react";
import { appeler } from "./api";
import { LIBELLE_ROLE } from "./roles.js";
import Cadre from "./Cadre.jsx";
import Pagination from "./Pagination.jsx";
import { usePagination } from "./usePagination.js";
import { Alerte, Avatar, Badge, Bouton, Chargement, MotDePasseTemp } from "./ui.jsx";

function dateHeure(iso) {
  const d = new Date(iso);
  return d.toLocaleDateString("fr-FR") + " à " + d.toLocaleTimeString("fr-FR", { hour: "2-digit", minute: "2-digit" });
}

export default function Reinitialisations() {
  const [liste, setListe] = useState(null);
  const pageDemandes = usePagination(liste, 5);
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
        <div className="flex animate-apparition flex-col items-center rounded-carte border border-dashed border-bord bg-white px-6 py-12 text-center">
          <span className="flex h-14 w-14 items-center justify-center rounded-2xl bg-baobab-50 text-baobab">
            <ShieldCheck className="h-7 w-7" aria-hidden="true" />
          </span>
          <p className="mt-3 text-sm text-slate-600">Aucune demande en attente.</p>
        </div>
      )}
      <div key={pageDemandes.page} className="grid animate-apparition gap-4">
      {liste && pageDemandes.elements.map((d) => (
        <article key={d.id} className="rounded-carte border border-bord border-l-4 border-l-soleil bg-white p-5 transition duration-300 hover:shadow-md sm:p-6">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div className="flex items-center gap-3">
              <Avatar nom={d.nom_complet} taille="h-12 w-12 text-base" />
              <h2 className="text-lg font-bold text-encre">{d.nom_complet}</h2>
            </div>
            <Badge ton="orange">En attente</Badge>
          </div>
          <dl className="mt-5 grid gap-3 text-sm sm:grid-cols-2 lg:grid-cols-3">
            {[
              [Mail, "E-mail", d.email],
              [UserCog, "Rôle", LIBELLE_ROLE[d.role] || d.role],
              ...(d.gestionnaire ? [[Users, "Gestionnaire du client", d.gestionnaire]] : []),
              [Phone, "Téléphone indiqué", d.contact || "—"],
              [Clock, "Demandé le", dateHeure(d.cree_le)],
            ].map(([Icone, libelle, valeur]) => (
              <div key={libelle} className="flex items-start gap-3 rounded-xl bg-fond p-3">
                <Icone className="mt-0.5 h-4 w-4 shrink-0 text-marque-600" aria-hidden="true" />
                <div className="min-w-0">
                  <dt className="text-xs uppercase text-slate-500">{libelle}</dt>
                  <dd className="truncate font-medium text-encre">{valeur}</dd>
                </div>
              </div>
            ))}
          </dl>
          <div className="mt-5 flex flex-wrap gap-2 border-t border-bord pt-4">
            <Bouton variante={confirmer === d.id ? "danger" : "primaire"} className="gap-1.5" onClick={() => traiter(d)}>
              <KeyRound className="h-4 w-4" aria-hidden="true" />
              {confirmer === d.id ? "Identité vérifiée : confirmer ?" : "Générer un mot de passe temporaire"}
            </Bouton>
            <Bouton variante="secondaire" className="gap-1.5" onClick={() => rejeter(d)}>
              <X className="h-4 w-4" aria-hidden="true" />
              Rejeter
            </Bouton>
          </div>
        </article>
      ))}
      </div>
      {liste && <Pagination {...pageDemandes} />}
    </Cadre>
  );
}
