import { CircleAlert, Lightbulb, MessageSquareText, Route } from "lucide-react";

// Retour au client après un refus ou un accord réduit : pourquoi, et quoi changer pour la prochaine demande.
// Le même contenu est montré au client, à l'agent et au directeur. `personnel` ajoute, pour le personnel
// seulement, le risque et l'endettement de chaque plan (jamais montrés au client).

function pct(x) {
  return (Number(x) * 100).toFixed(1).replace(".", ",") + " %";
}

function Titre({ icone: Icone, children }) {
  return (
    <h3 className="flex items-center gap-2 text-sm font-semibold text-encre">
      <Icone className="h-4 w-4 shrink-0 text-marque-700" aria-hidden="true" />
      {children}
    </h3>
  );
}

export default function RetourClient({ retour, personnel = false }) {
  if (!retour) return null;
  const { message, motifs = [], plans = [], institution = [], bloque, calcule } = retour;
  const accordReduit = retour.decision === "accorder_modifie";

  return (
    <div className="space-y-5">
      {(message || motifs.length > 0) && (
        <div className="space-y-2">
          <Titre icone={CircleAlert}>
            {accordReduit ? "Pourquoi le montant demandé n'a pas été accordé en entier" : "Pourquoi la demande n'a pas été acceptée"}
          </Titre>
          <ul className="space-y-1.5">
            {message && (
              <li className="flex items-start gap-2 rounded-champ bg-risque-moyen-fond px-3 py-2.5 text-sm text-texte">
                <MessageSquareText className="mt-0.5 h-4 w-4 shrink-0 text-risque-moyen" aria-hidden="true" />
                <span>{message}{personnel && <span className="text-texte-doux"> (motif écrit par le directeur)</span>}</span>
              </li>
            )}
            {motifs.map((m) => (
              <li key={m} className="rounded-champ bg-risque-moyen-fond px-3 py-2.5 text-sm text-texte">{m}</li>
            ))}
          </ul>
        </div>
      )}

      {plans.length > 0 && (
        <div className="space-y-2">
          <Titre icone={Route}>
            {accordReduit ? "Pour obtenir le montant entier la prochaine fois" : "Ce qui permettrait d'accepter une prochaine demande"}
          </Titre>
          <ol className="grid gap-2 md:grid-cols-2 xl:grid-cols-3">
            {plans.map((p, i) => (
              <li key={i} className="rounded-champ border border-marque-200 bg-marque-50 p-3 text-sm text-texte">
                <p className="text-xs font-semibold uppercase tracking-wide text-marque-700">Possibilité {i + 1}</p>
                <p className="mt-1">{p.texte}</p>
                {personnel && p.p_defaut != null && (
                  <p className="mt-2 text-xs text-texte-doux">
                    Risque {pct(p.p_defaut)} · mensualité {pct(p.endettement)} du revenu visé
                  </p>
                )}
              </li>
            ))}
          </ol>
        </div>
      )}
      {!bloque && calcule && plans.length === 0 && motifs.length > 0 && !accordReduit && (
        <p className="text-sm text-texte-doux">
          Aucun ajustement du montant, de la durée ou des revenus ne suffit pour le moment. Les conseils ci-dessous
          renforceront une prochaine demande.
        </p>
      )}

      {institution.length > 0 && (
        <div className="space-y-2">
          <Titre icone={Lightbulb}>{bloque ? "À faire avant toute nouvelle demande" : "Conseils pour renforcer votre dossier"}</Titre>
          <ul className="grid gap-2 md:grid-cols-2">
            {institution.map((c) => (
              <li key={c.code} className="rounded-champ border border-bord bg-fond px-3 py-2.5 text-sm text-texte">
                <p className="font-semibold text-encre">{c.titre}</p>
                <p className="mt-0.5">{c.texte}</p>
              </li>
            ))}
          </ul>
        </div>
      )}

    </div>
  );
}
