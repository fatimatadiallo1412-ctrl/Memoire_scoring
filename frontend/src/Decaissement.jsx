import { useEffect, useState } from "react";
import { appeler } from "./api";
import { dateFr, fcfa } from "./formats.js";
import { MARQUE } from "./marque.js";

const MODES = [
  ["especes", "Espèces"],
  ["mobile_money", "Mobile money"],
  ["virement", "Virement bancaire"],
];
const LIBELLE_MODE = Object.fromEntries(MODES);

const pct = (x) => (Number(x) * 100).toFixed(1).replace(".", ",") + " %";
const aujourdhui = () => new Date().toISOString().slice(0, 10);

function nomClient(c) {
  if (!c) return "—";
  return c.nom_complet || [c.prenom, c.nom].filter(Boolean).join(" ") || "Client n° " + c.id;
}

function Ligne({ libelle, children }) {
  return (
    <div className="flex justify-between gap-4 py-1.5 border-b border-slate-100 text-sm">
      <span className="text-slate-500">{libelle}</span>
      <span className="font-medium text-slate-900 text-right">{children}</span>
    </div>
  );
}

export function PanneauDecaissement({ demandeId, client, onFermer, onFini }) {
  const [date, setDate] = useState(aujourdhui());
  const [mode, setMode] = useState("");
  const [reference, setReference] = useState("");
  const [confirme, setConfirme] = useState(false);
  const [apercu, setApercu] = useState(null);
  const [erreur, setErreur] = useState("");
  const [envoi, setEnvoi] = useState(false);

  useEffect(() => {
    if (!date) return;
    let actif = true;
    appeler("/demandes/" + demandeId + "/apercu-decaissement", { params: { date_decaissement: date } })
      .then((r) => { if (actif) { setApercu(r); setErreur(""); } })
      .catch((e) => { if (actif) setErreur(e.message); });
    return () => { actif = false; };
  }, [demandeId, date]);

  const refRequise = mode !== "" && mode !== "especes";
  const pret = apercu && date && mode && confirme && (!refRequise || reference.trim().length >= 4);

  async function valider() {
    setEnvoi(true);
    setErreur("");
    try {
      await appeler("/demandes/" + demandeId + "/decaisser", {
        methode: "POST",
        json: { date_decaissement: date, mode_decaissement: mode, reference: reference.trim() || null },
      });
      onFini();
    } catch (e) {
      setErreur(e.message);
      setEnvoi(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center overflow-y-auto bg-slate-900/50 p-4">
      <div className="w-full max-w-2xl rounded-xl bg-white p-5 shadow-xl my-6">
        <h2 className="text-lg font-semibold text-marque">Confirmer le décaissement</h2>
        <p className="text-sm text-slate-500 mb-3">
          Vérifiez les conditions ci-dessous. L'opération est définitive : elle crée le crédit et son calendrier.
        </p>

        {apercu && (
          <div className="mb-4">
            <Ligne libelle="Client">{nomClient(client)}</Ligne>
            <Ligne libelle="Montant accordé">{fcfa(apercu.montant)}</Ligne>
            <Ligne libelle="Durée">{apercu.duree_mois} mois</Ligne>
            <Ligne libelle="Taux annuel">{pct(apercu.taux_annuel)}</Ligne>
            <Ligne libelle="Mensualité">{fcfa(apercu.mensualite)}</Ligne>
            <Ligne libelle="Total à rembourser">{fcfa(apercu.total_a_rembourser)}</Ligne>
            <Ligne libelle="Coût du crédit (intérêts)">{fcfa(apercu.cout_credit)}</Ligne>
          </div>
        )}

        <div className="grid gap-3 sm:grid-cols-2">
          <label className="text-sm">
            Date de décaissement
            <input type="date" value={date} min={apercu?.date_min || undefined} max={aujourdhui()}
                   onChange={(e) => setDate(e.target.value)}
                   className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2" />
          </label>
          <label className="text-sm">
            Mode de versement
            <select value={mode} onChange={(e) => setMode(e.target.value)}
                    className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2">
              <option value="">— Choisir —</option>
              {MODES.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
            </select>
          </label>
          {refRequise && (
            <label className="text-sm sm:col-span-2">
              Référence de la transaction (obligatoire)
              <input value={reference} maxLength={60} onChange={(e) => setReference(e.target.value)}
                     placeholder="N° de transaction mobile money ou de virement"
                     className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2" />
            </label>
          )}
        </div>

        {apercu && (
          <details className="mt-4">
            <summary className="cursor-pointer text-sm font-medium text-marque">
              Aperçu du calendrier ({apercu.calendrier.length} échéances)
            </summary>
            <div className="mt-2 max-h-56 overflow-auto rounded-lg border border-slate-200">
              <table className="w-full text-sm">
                <thead className="sticky top-0 bg-slate-50 text-left text-slate-500">
                  <tr><th className="p-2">N°</th><th className="p-2">Date</th>
                      <th className="p-2 text-right">Capital</th><th className="p-2 text-right">Intérêts</th>
                      <th className="p-2 text-right">À payer</th></tr>
                </thead>
                <tbody>
                  {apercu.calendrier.map((l) => (
                    <tr key={l.numero} className="border-t border-slate-100">
                      <td className="p-2">{l.numero}</td><td className="p-2">{dateFr(l.date_echeance)}</td>
                      <td className="p-2 text-right">{fcfa(l.capital)}</td>
                      <td className="p-2 text-right">{fcfa(l.interet)}</td>
                      <td className="p-2 text-right font-medium">{fcfa(l.montant_du)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </details>
        )}

        <label className="mt-4 flex items-start gap-2 text-sm">
          <input type="checkbox" checked={confirme} onChange={(e) => setConfirme(e.target.checked)} className="mt-1" />
          <span>Je confirme avoir remis les fonds au client dans les conditions indiquées. Cette opération est définitive.</span>
        </label>

        {erreur && <p className="mt-3 rounded-lg bg-red-50 p-2 text-sm text-red-700">{erreur}</p>}

        <div className="mt-4 flex justify-end gap-2">
          <button type="button" onClick={onFermer} disabled={envoi}
                  className="rounded-lg border border-slate-300 px-4 py-2 text-sm">Annuler</button>
          <button type="button" onClick={valider} disabled={!pret || envoi}
                  className="rounded-lg bg-marque px-4 py-2 text-sm font-medium text-white disabled:opacity-40">
            {envoi ? "Enregistrement…" : "Confirmer le décaissement"}
          </button>
        </div>
      </div>
    </div>
  );
}

export function EncadreDecaissement({ credit, client }) {
  const [det, setDet] = useState(null);

  useEffect(() => {
    appeler("/credits/" + credit.id + "/decaissement").then(setDet).catch(() => setDet(null));
  }, [credit.id]);

  if (!det) return null;
  const mode = LIBELLE_MODE[det.mode_decaissement] || "Non renseigné";

  return (
    <section className="mt-4 rounded-xl border border-slate-200 bg-white p-4">
      <style>{`
        .recu-impression { display: none; }
        @media print {
          body * { visibility: hidden; }
          .recu-impression, .recu-impression * { visibility: visible; }
          .recu-impression { display: block !important; position: absolute; left: 0; top: 0; width: 100%; padding: 32px; }
        }
      `}</style>

      <h2 className="text-base font-semibold text-marque mb-2">Décaissement</h2>
      <Ligne libelle="Date">{dateFr(det.date_decaissement)}</Ligne>
      <Ligne libelle="Mode de versement">{mode}</Ligne>
      {det.reference_decaissement && <Ligne libelle="Référence">{det.reference_decaissement}</Ligne>}
      <Ligne libelle="Décaissé par">{det.decaisse_par || "—"}</Ligne>
      <button type="button" onClick={() => window.print()}
              className="mt-3 rounded-lg border border-marque px-3 py-2 text-sm text-marque">
        Imprimer le reçu
      </button>
      <p className="mt-1 text-xs text-slate-400">Dans la fenêtre d'impression, choisissez « Enregistrer au format PDF » pour un fichier.</p>

      <div className="recu-impression">
        <h1 style={{ fontSize: 22, fontWeight: 700 }}>{MARQUE?.nom || "Microfinance"}</h1>
        <h2 style={{ fontSize: 18, margin: "12px 0" }}>Reçu de décaissement n° {det.credit_id}</h2>
        <table style={{ width: "100%", fontSize: 14, borderCollapse: "collapse" }}>
          <tbody>
            {[
              ["Client", nomClient(client)],
              ["Date de décaissement", dateFr(det.date_decaissement)],
              ["Montant décaissé", fcfa(det.montant_accorde)],
              ["Durée", det.duree_mois + " mois"],
              ["Taux annuel", pct(det.taux_annuel)],
              ["Mensualité", fcfa(det.mensualite)],
              ["Mode de versement", mode],
              ["Référence", det.reference_decaissement || "—"],
              ["Agent", det.decaisse_par || "—"],
            ].map(([l, v]) => (
              <tr key={l}>
                <td style={{ padding: "6px 0", borderBottom: "1px solid #ddd", width: "40%" }}>{l}</td>
                <td style={{ padding: "6px 0", borderBottom: "1px solid #ddd", fontWeight: 600 }}>{v}</td>
              </tr>
            ))}
          </tbody>
        </table>
        <div style={{ display: "flex", justifyContent: "space-between", marginTop: 70, fontSize: 13 }}>
          <div>Signature du client<br /><br /><br />____________________</div>
          <div>Signature de l'agent<br /><br /><br />____________________</div>
        </div>
      </div>
    </section>
  );
}
