import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { appeler } from "./api";
import { dateFr, fcfa } from "./formats.js";
import Cadre from "./Cadre.jsx";

function joli(texte) {
  const t = String(texte).replace(/_/g, " ");
  return t.charAt(0).toUpperCase() + t.slice(1);
}

export default function CreditClient() {
  const { id } = useParams();
  const [situation, setSituation] = useState(null);
  const [credit, setCredit] = useState(null);
  const [erreur, setErreur] = useState("");

  useEffect(() => {
    Promise.all([appeler("/moi/credits/" + id + "/situation"), appeler("/moi/credits")])
      .then(([s, liste]) => {
        setSituation(s);
        setCredit(liste.find((c) => String(c.id) === id) || null);
      })
      .catch((e) => setErreur(e.message));
  }, [id]);

  if (erreur) {
    return (
      <Cadre titre="Mon crédit">
        <p className="erreur">{erreur}</p>
        <Link to="/espace">Retour</Link>
      </Cadre>
    );
  }
  if (!situation) {
    return (
      <Cadre titre="Mon crédit">
        <p className="discret">Chargement…</p>
      </Cadre>
    );
  }

  const pourcentage = situation.total_du > 0 ? Math.round((100 * situation.total_paye) / situation.total_du) : 0;

  return (
    <Cadre titre="Mon crédit">
      <section className="panneau">
        <h2>
          Situation {situation.solde && <span className="badge vert">Soldé</span>}
          {!situation.solde && situation.nb_echeances_en_retard > 0 && <span className="badge rouge">En retard</span>}
        </h2>
        <div className="barre"><div className="barre-remplie" style={{ width: pourcentage + "%" }} /></div>
        <p className="discret">{pourcentage} % du total déjà payé</p>
        <dl className="grille-info">
          {credit && <div><dt>Montant accordé</dt><dd>{fcfa(credit.montant_accorde)}</dd></div>}
          {credit && <div><dt>Mensualité</dt><dd>{fcfa(credit.mensualite)}</dd></div>}
          {credit && <div><dt>Taux annuel</dt><dd>{credit.taux_annuel} %</dd></div>}
          <div><dt>Total à rembourser</dt><dd>{fcfa(situation.total_du)}</dd></div>
          <div><dt>Déjà payé</dt><dd>{fcfa(situation.total_paye)}</dd></div>
          <div><dt>Reste à payer</dt><dd>{fcfa(situation.reste_a_payer)}</dd></div>
          <div><dt>Capital restant</dt><dd>{fcfa(situation.capital_restant)}</dd></div>
          {situation.nb_echeances_en_retard > 0 && (
            <div><dt>Échéances en retard</dt><dd>{situation.nb_echeances_en_retard} ({fcfa(situation.montant_en_retard)})</dd></div>
          )}
          {situation.jours_retard_max > 0 && (
            <div><dt>Retard le plus long</dt><dd>{situation.jours_retard_max} jour(s)</dd></div>
          )}
        </dl>
      </section>

      <section className="panneau">
        <h2>Échéances</h2>
        <table className="tableau">
          <thead>
            <tr><th>N°</th><th>Date</th><th>À payer</th><th>Payé</th><th>Reste</th><th>État</th></tr>
          </thead>
          <tbody>
            {situation.echeances.map((e) => (
              <tr key={e.numero}>
                <td>{e.numero}</td>
                <td>{dateFr(e.date_echeance)}</td>
                <td>{fcfa(e.montant_du)}</td>
                <td>{fcfa(e.montant_paye)}</td>
                <td>{fcfa(e.reste_du)}</td>
                <td>
                  <span className={e.jours_retard > 0 ? "badge rouge" : "badge"}>
                    {joli(e.statut)}{e.jours_retard > 0 ? " (" + e.jours_retard + " j)" : ""}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
      <p><Link to="/espace">Retour à mon espace</Link></p>
    </Cadre>
  );
}
