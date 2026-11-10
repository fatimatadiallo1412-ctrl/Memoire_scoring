import { useEffect, useRef, useState } from "react";
import { appeler } from "./api";
import { Bouton, Panneau, classeSaisie } from "./ui.jsx";

const SUGGESTIONS = [
  "Quelle est la situation de ce client ?",
  "A-t-il du retard de paiement ?",
  "Quelle est sa prochaine échéance ?",
  "Peut-il refaire un crédit ?",
];

export default function AssistantPersonnel({ clientId }) {
  const [messages, setMessages] = useState([]);
  const [saisie, setSaisie] = useState("");
  const [attente, setAttente] = useState(false);
  const bas = useRef(null);

  useEffect(() => {
    setMessages([]);
  }, [clientId]);

  useEffect(() => {
    if (messages.length > 0 && bas.current) bas.current.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }, [messages]);

  async function envoyer(texte) {
    const propre = texte.trim();
    if (!propre || attente) return;
    setMessages((m) => [...m, { de: "moi", texte: propre }]);
    setSaisie("");
    setAttente(true);
    try {
      const r = await appeler("/assistant/personnel", {
        methode: "POST",
        json: { client_id: clientId, message: propre },
      });
      setMessages((m) => [...m, { de: "assistant", texte: r.reponse, intention: r.intention, confiance: r.confiance }]);
    } catch (e) {
      setMessages((m) => [...m, { de: "assistant", texte: "Erreur : " + e.message }]);
    } finally {
      setAttente(false);
    }
  }

  return (
    <Panneau titre="Assistant sur ce client">
      <p className="mb-3 text-sm text-slate-500">
        Posez une question en français sur ce client. L'assistant ne répond que pour ce client et ne remplace pas
        l'étude du dossier.
      </p>
      <div className="mb-3 flex flex-wrap gap-2">
        {SUGGESTIONS.map((s) => (
          <button key={s} type="button" disabled={attente} onClick={() => envoyer(s)}
            className="rounded-full bg-slate-100 px-3 py-1.5 text-xs text-slate-700 hover:bg-slate-200 disabled:opacity-50">
            {s}
          </button>
        ))}
      </div>

      {messages.length > 0 && (
        <div className="mb-3 grid max-h-96 gap-2 overflow-y-auto rounded-lg bg-slate-50 p-3">
          {messages.map((m, i) => (
            <div key={i} className={m.de === "moi" ? "justify-self-end" : "justify-self-start"}>
              <div className={"max-w-prose whitespace-pre-wrap rounded-xl px-3 py-2 text-sm " +
                (m.de === "moi" ? "bg-marque-700 text-white" : "bg-white text-slate-800 ring-1 ring-slate-200")}>
                {m.texte}
              </div>
              {m.intention && (
                <p className="mt-0.5 text-[11px] text-slate-400">
                  Intention détectée : {m.intention}
                  {m.confiance != null && !Number.isNaN(Number(m.confiance)) &&
                    " (confiance " + Math.round(Number(m.confiance) * 100) + " %)"}
                </p>
              )}
            </div>
          ))}
          {attente && <div className="text-sm text-slate-400">…</div>}
          <div ref={bas} />
        </div>
      )}

      <form className="flex gap-2" onSubmit={(e) => { e.preventDefault(); envoyer(saisie); }}>
        <input className={classeSaisie} value={saisie} maxLength={300} autoComplete="off"
          placeholder="Votre question…" onChange={(e) => setSaisie(e.target.value)} />
        <Bouton type="submit" disabled={attente || !saisie.trim()}>Envoyer</Bouton>
      </form>
    </Panneau>
  );
}
