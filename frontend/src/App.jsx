import { useEffect } from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import { lireJeton } from "./api";
import { useAuth } from "./useAuth.js";
import { ACCUEIL, accueilDe } from "./roles.js";
import Connexion from "./Connexion.jsx";
import Clients from "./Clients.jsx";
import FicheClient from "./FicheClient.jsx";
import NouveauClient from "./NouveauClient.jsx";
import NouvelleDemande from "./NouvelleDemande.jsx";
import Dossiers from "./Dossiers.jsx";
import FicheDossier from "./FicheDossier.jsx";
import Metiers from "./Metiers.jsx";
import Espace from "./Espace.jsx";
import CreditClient from "./CreditClient.jsx";
import CreditPersonnel from "./CreditPersonnel.jsx";
import AssistantClient from "./AssistantClient.jsx";
import Accueil from "./Accueil.jsx";
import Produits from "./Produits.jsx";
import Contact from "./Contact.jsx";
import Messages from "./Messages.jsx";
import Comptes from "./Comptes.jsx";
import MotDePasseOublie from "./MotDePasseOublie.jsx";
import Reinitialisations from "./Reinitialisations.jsx";
import ChangerMotDePasse from "./ChangerMotDePasse.jsx";
import Parametres from "./Parametres.jsx";
import Rapports from "./Rapports.jsx";
import TableauBord from "./TableauBord.jsx";
import SanteModele from "./SanteModele.jsx";

const PERSONNEL = ["agent_credit", "decideur"];
const SAISIE = ["agent_credit"];
const RESPONSABLES = ["decideur"];
const CLIENT = ["client"];

function Protegee({ roles, children }) {
  const { utilisateur, chargement } = useAuth();
  if (chargement) return <p className="centre">Chargement…</p>;
  if (!utilisateur) return <Navigate to="/connexion" replace />;
  if (utilisateur.doit_changer_mdp) return <Navigate to="/changer-mot-de-passe" replace />;
  if (!roles.includes(utilisateur.role)) return <Navigate to={ACCUEIL[utilisateur.role]} replace />;
  return children;
}

function Connectee({ children }) {
  const { utilisateur, chargement } = useAuth();
  if (chargement) return <p className="centre">Chargement…</p>;
  if (!utilisateur) return <Navigate to="/connexion" replace />;
  return children;
}

// Pages publiques (site, connexion) : y arriver ferme la session. Pour revenir dans son espace,
// l'utilisateur doit ressaisir son identifiant et son mot de passe. La session est aussi perdue
// à la fermeture de l'onglet (jeton conservé dans sessionStorage).
function Publique({ children }) {
  const { deconnecter } = useAuth();
  // Une seule fois, à l'arrivée sur la page : une connexion faite ensuite sur cette page est conservée.
  useEffect(() => {
    if (lireJeton()) deconnecter();
  }, [deconnecter]);
  return children;
}

function Racine() {
  const { utilisateur, chargement } = useAuth();
  if (chargement) return <p className="centre">Chargement…</p>;
  return <Navigate to={utilisateur ? accueilDe(utilisateur) : "/connexion"} replace />;
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Publique><Accueil /></Publique>} />
      <Route path="/produits" element={<Publique><Produits /></Publique>} />
      <Route path="/contact" element={<Publique><Contact /></Publique>} />
      <Route path="/connexion" element={<Publique><Connexion /></Publique>} />
      <Route path="/clients" element={<Protegee roles={PERSONNEL}><Clients /></Protegee>} />
      <Route path="/clients/nouveau" element={<Protegee roles={SAISIE}><NouveauClient /></Protegee>} />
      <Route path="/clients/:id" element={<Protegee roles={PERSONNEL}><FicheClient /></Protegee>} />
      <Route path="/demandes/nouvelle" element={<Protegee roles={SAISIE}><NouvelleDemande /></Protegee>} />
      <Route path="/dossiers" element={<Protegee roles={PERSONNEL}><Dossiers /></Protegee>} />
      <Route path="/dossiers/:id" element={<Protegee roles={PERSONNEL}><FicheDossier /></Protegee>} />
      <Route path="/metiers" element={<Protegee roles={RESPONSABLES}><Metiers /></Protegee>} />
      <Route path="/parametres" element={<Protegee roles={PERSONNEL}><Parametres /></Protegee>} />
      <Route path="/tableau-de-bord" element={<Protegee roles={RESPONSABLES}><TableauBord /></Protegee>} />
      <Route path="/rapports" element={<Protegee roles={RESPONSABLES}><Rapports /></Protegee>} />
      <Route path="/changer-mot-de-passe" element={<Connectee><ChangerMotDePasse /></Connectee>} />
      <Route path="/mot-de-passe-oublie" element={<Publique><MotDePasseOublie /></Publique>} />
      <Route path="/reinitialisations" element={<Protegee roles={["administrateur"]}><Reinitialisations /></Protegee>} />
      <Route path="/comptes" element={<Protegee roles={["administrateur"]}><Comptes /></Protegee>} />
      <Route path="/messages" element={<Protegee roles={["administrateur"]}><Messages /></Protegee>} />
      <Route path="/sante-modele" element={<Protegee roles={["administrateur"]}><SanteModele /></Protegee>} />
      <Route path="/espace" element={<Protegee roles={CLIENT}><Espace /></Protegee>} />
      <Route path="/espace/credits/:id" element={<Protegee roles={CLIENT}><CreditClient /></Protegee>} />
      <Route path="/espace/assistant" element={<Protegee roles={CLIENT}><AssistantClient /></Protegee>} />
      <Route path="/credits/:id" element={<Protegee roles={PERSONNEL}><CreditPersonnel /></Protegee>} />
      <Route path="*" element={<Racine />} />
    </Routes>
  );
}
