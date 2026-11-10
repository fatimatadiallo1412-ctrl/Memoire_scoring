import { useEffect, useRef, useState } from "react";
import { appeler } from "./api";
import Cadre from "./Cadre.jsx";

const SUGGESTIONS = [
  "Quelle est ma prochaine échéance ?",
  "Combien me reste-t-il à payer ?",
  "Est-ce que j'ai du retard ?",
  "Puis-je refaire un crédit ?",
];

export default function AssistantClient() {
  const [messages, setMessages] = useState([
    { de: "assistant", texte: "Bonjour ! Posez-moi une question sur votre compte : prochaine échéance, solde, retard, historique, nouveau crédit." },
  ]);
  const [saisie, setSaisie] = useState("");
  const [attente, setAttente] = useState(false);
  const bas = useRef(null);

  useEffect(() => {
    if (bas.current) bas.current.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function envoyer(texte) {
    const propre = texte.trim();
    if (!propre || attente) return;
    setMessages((m) => [...m, { de: "moi", texte: propre }]);
    setSaisie("");
    setAttente(true);
    try {
      const reponse = await appeler("/moi/assistant", { methode: "POST", json: { message: propre } });
      setMessages((m) => [...m, { de: "assistant", texte: reponse.reponse }]);
    } catch (e) {
      setMessages((m) => [...m, { de: "assistant", texte: "Désolé, une erreur est survenue : " + e.message }]);
    } finally {
      setAttente(false);
    }
  }

  return (
    <Cadre titre="Assistant">
      <p className="discret">
        L'assistant répond aux questions sur votre propre compte. Le texte de vos questions n'est pas conservé.
      </p>
      <div className="suggestions">
        {SUGGESTIONS.map((s) => (
          <button key={s} type="button" onClick={() => envoyer(s)} disabled={attente}>{s}</button>
        ))}
      </div>
      <div className="conversation">
        {messages.map((m, i) => (
          <div key={i} className={"bulle " + m.de}>{m.texte}</div>
        ))}
        {attente && <div className="bulle assistant discret">…</div>}
        <div ref={bas} />
      </div>
      <form className="saisie-chat" onSubmit={(e) => { e.preventDefault(); envoyer(saisie); }}>
        <input value={saisie} onChange={(e) => setSaisie(e.target.value)} maxLength={300}
          placeholder="Votre question…" autoComplete="off" />
        <button type="submit" disabled={attente || !saisie.trim()}>Envoyer</button>
      </form>
    </Cadre>
  );
}
