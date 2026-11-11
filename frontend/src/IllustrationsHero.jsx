import { useId } from "react";

// Illustrations décoratives du hero (aplats uniquement, aucun dégradé, aucun texte).
// Scènes inspirées de la microfinance au Sénégal : commerçante au marché,
// évaluation du dossier, pirogue de pêcheur, suivi des échéances sur téléphone.
// Les animations sont neutralisées par la préférence « réduire les animations » (index.css).

const C = {
  nuit: "#121a4a",
  fond: "#212d84",
  bleu: "#2d3db3",
  bleuMoyen: "#3a4fd8",
  bleuClair: "#7085f0",
  bleuPale: "#c2cbfb",
  soleil: "#f5b70a",
  soleilClair: "#fcd34d",
  soleilFonce: "#b98a00",
  terre: "#e8603c",
  terreClair: "#f2875f",
  baobab: "#0f8a63",
  baobabClair: "#34b383",
  sable: "#faf6ef",
  sol: "#e8d5b5",
  bois: "#6b4a35",
  boisClair: "#a0703f",
  peau: "#8a5a3c",
  peauFonce: "#5e3b26",
  gris: "#d9dee6",
  grisClair: "#e9edf2",
  blanc: "#ffffff",
};

const SVG = "h-auto w-full";

function Cadre({ children, label }) {
  const id = useId().replace(/:/g, "");
  return (
    <svg viewBox="0 0 400 360" className={SVG} aria-hidden="true" focusable="false" data-scene={label}
      xmlns="http://www.w3.org/2000/svg">
      <defs>
        <clipPath id={"rond" + id}>
          <circle cx="200" cy="180" r="160" />
        </clipPath>
      </defs>
      <circle cx="200" cy="180" r="160" fill={C.fond} />
      <g clipPath={"url(#rond" + id + ")"}>{children}</g>
    </svg>
  );
}

function Piece({ x, y, r = 9, className = "", style }) {
  return (
    <g className={"svg-centre " + className} style={style}>
      <circle cx={x} cy={y} r={r} fill={C.soleil} />
      <circle cx={x} cy={y} r={r * 0.58} fill="none" stroke={C.soleilFonce} strokeWidth="1.8" />
    </g>
  );
}

function Coche({ cx, cy, taille = 4 }) {
  return (
    <path d={`M${cx - taille} ${cy} l${taille * 0.75} ${taille * 0.75} l${taille * 1.5} -${taille * 1.5}`}
      fill="none" stroke={C.blanc} strokeWidth="2.6" strokeLinecap="round" strokeLinejoin="round" />
  );
}

function Etincelle({ x, y, r = 6, delai = "0s" }) {
  return (
    <path className="animate-clignoter" style={{ animationDelay: delai, animationDuration: "2.4s" }}
      d={`M${x} ${y - r} Q${x} ${y} ${x + r} ${y} Q${x} ${y} ${x} ${y + r} Q${x} ${y} ${x - r} ${y} Q${x} ${y} ${x} ${y - r} Z`}
      fill={C.soleilClair} />
  );
}

// 1. Commerçante au marché, sous un baobab
export function SceneMarche() {
  return (
    <Cadre label="marche">
      {/* Soleil et rayons */}
      <g transform="translate(305 92)">
        <g className="animate-tourner svg-centre">
          {Array.from({ length: 8 }, (_, i) => (
            <rect key={i} x="-3" y="-48" width="6" height="13" rx="3" fill={C.soleil} transform={`rotate(${i * 45})`} />
          ))}
        </g>
        <circle r="26" fill={C.soleil} />
      </g>

      {/* Sol */}
      <rect x="0" y="282" width="400" height="80" fill={C.sol} />

      {/* Baobab */}
      <g>
        <path d="M66 288 C72 240 70 200 62 168 L100 168 C92 200 90 240 98 288 Z" fill={C.bois} />
        <path d="M68 174 L46 146 M95 172 L118 144 M82 170 L82 138" stroke={C.bois} strokeWidth="7" strokeLinecap="round" />
        <g className="animate-flotter" style={{ animationDuration: "8s" }}>
          <ellipse cx="44" cy="138" rx="26" ry="14" fill={C.baobab} />
          <ellipse cx="82" cy="128" rx="30" ry="17" fill={C.baobab} />
          <ellipse cx="120" cy="138" rx="26" ry="14" fill={C.baobab} />
          <ellipse cx="76" cy="122" rx="14" ry="7" fill={C.baobabClair} />
        </g>
      </g>

      {/* Poteaux et auvent rayé */}
      <rect x="158" y="150" width="6" height="135" fill={C.bois} />
      <rect x="336" y="150" width="6" height="135" fill={C.bois} />
      <rect x="150" y="126" width="200" height="26" rx="4" fill={C.terre} />
      {[170, 210, 250, 290, 330].map((x) => (
        <rect key={x} x={x} y="126" width="20" height="26" fill={C.sable} />
      ))}
      {Array.from({ length: 10 }, (_, i) => (
        <circle key={i} cx={160 + i * 20} cy="152" r="10" fill={i % 2 ? C.sable : C.terre} />
      ))}

      {/* Commerçante */}
      <g>
        <path d="M218 288 L224 224 C226 213 236 207 250 207 C264 207 274 213 276 224 L282 288 Z" fill={C.baobab} />
        {[[236, 232], [250, 246], [264, 232], [242, 262], [258, 262], [250, 222]].map(([x, y]) => (
          <circle key={x + "-" + y} cx={x} cy={y} r="3.2" fill={C.soleil} />
        ))}
        <rect x="245" y="194" width="10" height="16" fill={C.peau} />
        <circle cx="250" cy="184" r="17" fill={C.peau} />
        <path d="M231 181 C227 155 273 153 269 179 Q250 168 231 181 Z" fill={C.soleil} />
        <ellipse cx="267" cy="160" rx="9" ry="7" fill={C.soleilClair} />
        <circle cx="243" cy="169" r="2.2" fill={C.terre} />
        <circle cx="256" cy="166" r="2.2" fill={C.terre} />
        <circle cx="233.5" cy="191" r="2.6" fill={C.soleil} />
        <path d="M226 228 Q212 252 228 268 M274 228 Q288 252 272 268" fill="none" stroke={C.peau} strokeWidth="9" strokeLinecap="round" />
      </g>

      {/* Étal et nappe */}
      <rect x="148" y="266" width="204" height="16" rx="3" fill={C.bois} />
      <rect x="158" y="282" width="184" height="32" fill={C.terreClair} />
      {[172, 212, 252, 292].map((x) => (
        <rect key={x} x={x} y="282" width="14" height="32" fill={C.soleil} />
      ))}

      {/* Paniers : mangues et tomates */}
      <path d="M166 266 a24 13 0 0 0 48 0 Z" fill={C.boisClair} />
      <ellipse cx="179" cy="259" rx="8.5" ry="6.5" fill={C.soleil} />
      <ellipse cx="193" cy="256" rx="8.5" ry="6.5" fill={C.terreClair} />
      <ellipse cx="203" cy="261" rx="7.5" ry="5.5" fill={C.soleil} />
      <path d="M290 266 a24 13 0 0 0 48 0 Z" fill={C.boisClair} />
      {[[302, 259], [314, 256], [326, 259], [314, 249]].map(([x, y]) => (
        <circle key={x + "-" + y} cx={x} cy={y} r="6.5" fill={C.terre} />
      ))}

      {/* Pièces qui s'envolent */}
      <Piece x={300} y={232} className="animate-monter" />
      <Piece x={322} y={238} className="animate-monter" style={{ animationDelay: "1.5s" }} />
      <Piece x={284} y={240} r={7} className="animate-monter" style={{ animationDelay: "3s" }} />
    </Cadre>
  );
}

// 2. Évaluation du dossier : jauge de risque qui se stabilise dans le vert
export function SceneDecision() {
  return (
    <Cadre label="decision">
      <rect x="120" y="80" width="174" height="226" rx="16" fill={C.bleuMoyen} transform="rotate(-7 207 193)" />

      <g className="animate-flotter" style={{ animationDuration: "7s" }}>
        <rect x="112" y="70" width="186" height="232" rx="16" fill={C.blanc} />
        <circle cx="142" cy="101" r="14" fill={C.bleuPale} />
        <circle cx="142" cy="97" r="5" fill={C.bleu} />
        <path d="M133 110 a9 7 0 0 1 18 0 Z" fill={C.bleu} />
        <rect x="166" y="92" width="86" height="7" rx="3.5" fill={C.gris} />
        <rect x="166" y="105" width="54" height="6" rx="3" fill={C.grisClair} />

        {/* Jauge : vert / or / terre */}
        <path d="M147 200 A58 58 0 0 1 176 149.8" fill="none" stroke={C.baobab} strokeWidth="14" />
        <path d="M176 149.8 A58 58 0 0 1 234 149.8" fill="none" stroke={C.soleil} strokeWidth="14" />
        <path d="M234 149.8 A58 58 0 0 1 263 200" fill="none" stroke={C.terre} strokeWidth="14" />
        <g className="animate-aiguille" style={{ transformOrigin: "205px 200px" }}>
          <path d="M200.5 200 L205 154 L209.5 200 Z" fill={C.nuit} />
        </g>
        <circle cx="205" cy="200" r="9" fill={C.nuit} />
        <circle cx="205" cy="200" r="3.5" fill={C.blanc} />

        <rect x="138" y="222" width="134" height="7" rx="3.5" fill={C.grisClair} />
        <rect x="138" y="236" width="96" height="7" rx="3.5" fill={C.grisClair} />
        <rect x="138" y="258" width="78" height="26" rx="13" fill={C.baobab} />
        <Coche cx={156} cy={271} />
        <rect x="172" y="268" width="34" height="6" rx="3" fill={C.blanc} opacity="0.85" />
        <rect x="226" y="258" width="46" height="26" rx="13" fill={C.bleu} />
      </g>

      {/* Ampoule : la recommandation */}
      <g transform="translate(318 84)">
        <circle r="22" fill={C.soleil} opacity="0.4" className="animate-onde svg-centre" />
        <g className="animate-flotter" style={{ animationDelay: "0.6s" }}>
          <circle r="16" fill={C.soleil} />
          <rect x="-7" y="13" width="14" height="9" rx="2" fill={C.gris} />
          <path d="M-5 -2 l5 6 l5 -6" fill="none" stroke={C.soleilFonce} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
        </g>
      </g>

      {/* Pastille validée */}
      <g className="animate-flotter" style={{ animationDelay: "1.2s" }}>
        <circle cx="96" cy="250" r="20" fill={C.baobab} />
        <Coche cx={96} cy={251} taille={5} />
      </g>

      <Etincelle x={92} y={118} />
      <Etincelle x={322} y={252} r={7} delai="0.8s" />
      <Etincelle x={340} y={170} r={4} delai="1.6s" />
    </Cadre>
  );
}

function cheminVague(y, amplitude) {
  let d = `M0 ${y}`;
  for (let x = 0; x < 600; x += 80) d += ` q20 -${amplitude} 40 0 q20 ${amplitude} 40 0`;
  return d + " L600 380 L0 380 Z";
}

// 3. Pirogue de pêcheur au coucher du soleil
export function ScenePirogue() {
  return (
    <Cadre label="pirogue">
      <circle cx="200" cy="214" r="78" fill={C.soleil} opacity="0.18" />
      <circle cx="200" cy="214" r="54" fill={C.soleil} />

      {/* Oiseaux */}
      {[[90, 110, "0s"], [120, 92, "1s"], [296, 120, "2s"]].map(([x, y, delai]) => (
        <g key={x} className="animate-flotter" style={{ animationDelay: delai, animationDuration: "5s" }}>
          <path d={`M${x} ${y} q6 -6 12 0 q6 -6 12 0`} fill="none" stroke={C.blanc} strokeWidth="2.5" strokeLinecap="round" />
        </g>
      ))}

      {/* Mer, vague arrière */}
      <path d={cheminVague(226, 7)} fill={C.bleu} className="animate-vague" style={{ animationDuration: "9s" }} />
      <rect x="170" y="240" width="60" height="4" rx="2" fill={C.soleil} className="animate-clignoter" style={{ animationDuration: "3s" }} />
      <rect x="182" y="252" width="36" height="4" rx="2" fill={C.soleil} className="animate-clignoter" style={{ animationDuration: "3s", animationDelay: "1s" }} />

      {/* Pirogue peinte et pêcheur */}
      <g className="animate-balancer svg-centre">
        <line x1="140" y1="224" x2="140" y2="158" stroke={C.bois} strokeWidth="3.5" strokeLinecap="round" />
        <path d="M140 158 L172 167 L140 176 Z" fill={C.soleil} />

        <rect x="224" y="182" width="16" height="34" rx="7" fill={C.sable} />
        <circle cx="232" cy="171" r="9.5" fill={C.peauFonce} />
        <path d="M222 168 a10 7 0 0 1 20 0 Z" fill={C.terre} />
        <line x1="270" y1="138" x2="214" y2="250" stroke={C.bois} strokeWidth="4" strokeLinecap="round" />
        <path d="M228 192 L250 186 M236 200 L242 205" stroke={C.peauFonce} strokeWidth="6" strokeLinecap="round" />

        <path d="M92 220 C120 250 280 250 308 220 L322 200 C300 222 100 222 78 200 Z" fill={C.terre} />
        <path d="M86 212 C118 238 282 238 314 212 L311 220 C282 246 118 246 89 220 Z" fill={C.soleil} />
        <path d="M95 224 C122 248 278 248 305 224 L300 230 C276 252 124 252 100 230 Z" fill={C.baobab} />
        {[130, 170, 210, 250].map((x) => (
          <path key={x} d={`M${x} 222 l8 -8 l8 8 Z`} fill={C.sable} />
        ))}
      </g>

      {/* Mer, vagues avant */}
      <path d={cheminVague(244, 6)} fill={C.bleuMoyen} className="animate-vague" style={{ animationDuration: "6s" }} />
      <path d={cheminVague(290, 8)} fill={C.bleu} className="animate-vague"
        style={{ animationDuration: "11s", animationDirection: "reverse" }} />
    </Cadre>
  );
}

// 4. Suivi des échéances sur téléphone, rappel et assistant
export function SceneSuivi() {
  const lignes = [0, 1, 2, 3];
  return (
    <Cadre label="suivi">
      <g className="animate-flotter" style={{ animationDuration: "7s" }}>
        <rect x="135" y="42" width="140" height="280" rx="24" fill={C.nuit} />
        <rect x="146" y="60" width="118" height="246" rx="14" fill={C.blanc} />
        <path d="M146 74 a14 14 0 0 1 14 -14 h90 a14 14 0 0 1 14 14 v36 h-118 Z" fill={C.bleu} />
        <rect x="186" y="49" width="38" height="5" rx="2.5" fill={C.bleu} />
        <circle cx="166" cy="86" r="9" fill={C.bleuPale} />
        <rect x="182" y="80" width="56" height="6" rx="3" fill={C.blanc} opacity="0.85" />
        <rect x="182" y="91" width="34" height="5" rx="2.5" fill={C.blanc} opacity="0.5" />

        {lignes.map((i) => {
          const y = 122 + i * 42;
          const payee = i < 3;
          return (
            <g key={i}>
              <rect x="155" y={y} width="100" height="32" rx="8" fill="#f3f5f8" />
              {payee ? (
                <g className="animate-cocher svg-centre" style={{ animationDelay: i * 0.6 + "s" }}>
                  <circle cx="172" cy={y + 16} r="9" fill={C.baobab} />
                  <Coche cx={172} cy={y + 16} taille={3.6} />
                </g>
              ) : (
                <g>
                  <circle cx="172" cy={y + 16} r="9" fill={C.soleil} opacity="0.5" className="animate-onde svg-centre" />
                  <circle cx="172" cy={y + 16} r="9" fill={C.soleil} />
                </g>
              )}
              <rect x="188" y={y + 9} width="54" height="6" rx="3" fill={C.gris} />
              <rect x="188" y={y + 19} width="32" height="5" rx="2.5" fill={C.grisClair} />
            </g>
          );
        })}
        <rect x="186" y="294" width="38" height="4" rx="2" fill={C.gris} />
      </g>

      {/* Rappel : cloche qui sonne */}
      <g transform="translate(300 86)">
        <circle r="21" fill={C.soleil} />
        <g className="animate-sonner" style={{ transformOrigin: "0px -12px" }}>
          <path d="M0 -12 c-6.5 0 -10 4.5 -10 11 v6 l-4 5 h28 l-4 -5 v-6 c0 -6.5 -3.5 -11 -10 -11 Z" fill={C.blanc} />
          <circle cx="0" cy="13" r="3" fill={C.blanc} />
        </g>
        <circle cx="15" cy="-15" r="6" fill={C.terre} />
      </g>

      {/* Assistant : bulle qui écrit */}
      <g className="animate-flotter" style={{ animationDelay: "1.5s" }}>
        <rect x="56" y="196" width="72" height="40" rx="14" fill={C.blanc} />
        <path d="M110 234 l12 14 l-2 -16 Z" fill={C.blanc} />
        {[76, 92, 108].map((x, k) => (
          <circle key={x} cx={x} cy="216" r="4.5" fill={C.bleuClair} className="animate-clignoter"
            style={{ animationDelay: k * 0.2 + "s" }} />
        ))}
      </g>

      <g className="animate-flotter" style={{ animationDelay: "0.8s", animationDuration: "5s" }}>
        <Piece x={322} y={252} r={14} />
      </g>
      <Etincelle x={96} y={120} />
      <Etincelle x={330} y={180} r={5} delai="1s" />
    </Cadre>
  );
}

function Soleil({ x, y, r = 24 }) {
  return (
    <g transform={`translate(${x} ${y})`}>
      <g className="animate-tourner svg-centre">
        {Array.from({ length: 8 }, (_, i) => (
          <rect key={i} x="-2.5" y={-r - 18} width="5" height="11" rx="2.5" fill={C.soleil} transform={`rotate(${i * 45})`} />
        ))}
      </g>
      <circle r={r} fill={C.soleil} />
    </g>
  );
}

// 5. Couturier à sa machine : l'aiguille pique, le tissu wax avance, le volant tourne
export function SceneCouture() {
  const motif = [C.terre, C.soleil, C.baobab, C.sable];
  return (
    <Cadre label="couture">
      {/* Fanions de tissu */}
      <path d="M40 58 Q200 96 360 58" fill="none" stroke={C.bleuPale} strokeWidth="2" />
      {Array.from({ length: 8 }, (_, i) => {
        const x = 64 + i * 38;
        const y = 64 + Math.sin((i / 7) * Math.PI) * 14;
        return (
          <g key={i} className="animate-flotter" style={{ animationDelay: i * 0.25 + "s", animationDuration: "3.5s" }}>
            <path d={`M${x - 13} ${y} L${x + 13} ${y} L${x} ${y + 26} Z`} fill={motif[i % 4]} />
          </g>
        );
      })}

      {/* Couturier */}
      <path d="M72 300 L80 214 C82 200 94 194 110 194 C126 194 138 200 140 214 L148 300 Z" fill={C.bleuPale} />
      <path d="M96 214 L110 240 L124 214" fill="none" stroke={C.bleu} strokeWidth="3" strokeLinejoin="round" />
      <rect x="104" y="180" width="12" height="16" fill={C.peauFonce} />
      <circle cx="110" cy="168" r="17" fill={C.peauFonce} />
      <rect x="94" y="147" width="32" height="12" rx="4" fill={C.terre} />
      <path d="M134 222 Q160 236 172 238" fill="none" stroke={C.peauFonce} strokeWidth="9" strokeLinecap="round" />

      {/* Table et tissu qui avance */}
      <rect x="40" y="250" width="330" height="14" rx="3" fill={C.bois} />
      <rect x="70" y="264" width="10" height="70" fill={C.bois} />
      <rect x="330" y="264" width="10" height="70" fill={C.bois} />
      <g className="animate-vague" style={{ animationDuration: "3s" }}>
        {Array.from({ length: 22 }, (_, i) => (
          <rect key={i} x={150 + i * 20} y="240" width="20" height="10" fill={motif[i % 4]} />
        ))}
      </g>

      {/* Machine à coudre */}
      <rect x="168" y="226" width="150" height="16" rx="5" fill={C.blanc} />
      <rect x="276" y="152" width="32" height="80" rx="9" fill={C.blanc} />
      <rect x="180" y="148" width="128" height="28" rx="12" fill={C.blanc} />
      <rect x="180" y="148" width="28" height="56" rx="9" fill={C.blanc} />
      <rect x="214" y="158" width="52" height="8" rx="4" fill={C.bleuPale} />
      <rect x="234" y="130" width="12" height="18" rx="3" fill={C.terre} />
      <g className="animate-coudre">
        <rect x="192" y="202" width="3.5" height="20" rx="1.5" fill={C.nuit} />
      </g>
      <g transform="translate(314 168)">
        <g className="animate-tourner svg-centre" style={{ animationDuration: "2s" }}>
          <circle r="15" fill={C.soleil} />
          <rect x="-1.5" y="-13" width="3" height="26" fill={C.soleilFonce} />
          <rect x="-13" y="-1.5" width="26" height="3" fill={C.soleilFonce} />
        </g>
        <circle r="4" fill={C.blanc} />
      </g>
      <Etincelle x={340} y={110} r={6} />
    </Cadre>
  );
}

// 6. Champ : les pousses de mil grandissent sous l'arrosoir
export function SceneChamp() {
  const plants = [118, 158, 198, 238, 278];
  return (
    <Cadre label="champ">
      <Soleil x={110} y={96} />
      <ellipse cx="200" cy="350" rx="260" ry="96" fill={C.baobab} />
      <ellipse cx="80" cy="300" rx="140" ry="40" fill={C.baobabClair} />
      {[0, 1, 2].map((k) => (
        <path key={k} d={`M40 ${300 + k * 16} Q200 ${282 + k * 16} 360 ${300 + k * 16}`} fill="none" stroke={C.sol} strokeWidth="2.5" opacity="0.5" />
      ))}

      {plants.map((x, i) => (
        <g key={x} className="animate-pousser svg-bas" style={{ animationDelay: 0.3 + i * 0.25 + "s" }}>
          <path d={`M${x} 286 L${x} 222`} stroke={C.baobabClair} strokeWidth="4" strokeLinecap="round" />
          <path d={`M${x} 262 Q${x - 18} 252 ${x - 22} 236 Q${x - 4} 242 ${x} 258 Z`} fill={C.baobabClair} />
          <path d={`M${x} 248 Q${x + 18} 238 ${x + 22} 222 Q${x + 4} 228 ${x} 244 Z`} fill={C.baobabClair} />
          <ellipse cx={x} cy="212" rx="6" ry="14" fill={C.soleil} />
        </g>
      ))}

      {/* Arrosoir et gouttes */}
      <g className="animate-flotter" style={{ animationDuration: "4s" }}>
        <g transform="rotate(-18 300 150)">
          <rect x="276" y="132" width="52" height="40" rx="8" fill={C.terre} />
          <path d="M276 144 L238 128 L240 120 L278 134 Z" fill={C.terre} />
          <rect x="230" y="114" width="14" height="10" rx="3" fill={C.terreClair} />
          <path d="M328 140 q18 6 0 26" fill="none" stroke={C.terre} strokeWidth="5" />
        </g>
      </g>
      {[0, 1, 2, 3].map((k) => (
        <circle key={k} cx={222 + (k % 2) * 10} cy={150 + (k > 1 ? 8 : 0)} r="3.5" fill={C.bleuPale}
          className="animate-goutte" style={{ animationDelay: k * 0.4 + "s" }} />
      ))}
    </Cadre>
  );
}

// 7. Transfert d'argent entre deux téléphones
export function SceneTransfert() {
  const trajet = "M138 168 Q200 92 262 168";
  return (
    <Cadre label="transfert">
      {[[70, -8], [250, 8]].map(([x, angle], k) => (
        <g key={x} className="animate-flotter" style={{ animationDelay: k * 1.2 + "s" }}>
          <g transform={`rotate(${angle} ${x + 40} 220)`}>
            <rect x={x} y="150" width="80" height="150" rx="16" fill={C.nuit} />
            <rect x={x + 7} y="162" width="66" height="126" rx="10" fill={C.blanc} />
            <circle cx={x + 40} cy="196" r="14" fill={k ? C.baobab : C.bleuPale} />
            {k ? <Coche cx={x + 40} cy={197} taille={5} /> : <circle cx={x + 40} cy="192" r="5" fill={C.bleu} />}
            <rect x={x + 18} y="222" width="44" height="6" rx="3" fill={C.gris} />
            <rect x={x + 24} y="234" width="32" height="5" rx="2.5" fill={C.grisClair} />
            <rect x={x + 16} y="258" width="48" height="18" rx="9" fill={k ? C.baobab : C.soleil} />
          </g>
        </g>
      ))}
      <path d={trajet} fill="none" stroke={C.soleil} strokeWidth="3" strokeDasharray="8 8" strokeLinecap="round"
        className="animate-pointilles" />
      <g className="animate-transfert" style={{ offsetPath: `path("${trajet}")` }}>
        <circle r="13" fill={C.soleil} />
        <circle r="7.5" fill="none" stroke={C.soleilFonce} strokeWidth="2" />
      </g>
      {[0, 1].map((k) => (
        <circle key={k} cx="290" cy="128" r={12 + k * 10} fill="none" stroke={C.bleuPale} strokeWidth="2.5"
          className="animate-onde svg-centre" style={{ animationDelay: k * 0.6 + "s" }} />
      ))}
      <Etincelle x={110} y={110} />
      <Etincelle x={200} y={250} r={5} delai="0.7s" />
    </Cadre>
  );
}

// 8. Élevage : un mouton broute près de l'enclos
export function SceneElevage() {
  return (
    <Cadre label="elevage">
      <Soleil x={300} y={92} r={22} />
      <rect x="0" y="262" width="400" height="100" fill={C.baobabClair} />
      <rect x="0" y="262" width="400" height="10" fill={C.baobab} />
      {/* Enclos */}
      {[60, 110, 290, 340].map((x) => <rect key={x} x={x} y="200" width="9" height="70" rx="2" fill={C.bois} />)}
      <rect x="40" y="214" width="330" height="7" rx="3" fill={C.boisClair} />
      <rect x="40" y="240" width="330" height="7" rx="3" fill={C.boisClair} />
      {/* Botte de foin */}
      <rect x="282" y="236" width="70" height="38" rx="6" fill={C.soleil} />
      <path d="M294 236 v38 M318 236 v38 M342 236 v38" stroke={C.soleilFonce} strokeWidth="2" />

      {/* Mouton */}
      <g className="animate-balancer svg-centre" style={{ animationDuration: "3s" }}>
        <rect x="160" y="250" width="9" height="34" rx="4" fill={C.peauFonce} />
        <rect x="182" y="254" width="9" height="32" rx="4" fill={C.peauFonce} />
        <rect x="218" y="254" width="9" height="32" rx="4" fill={C.peauFonce} />
        <rect x="238" y="250" width="9" height="34" rx="4" fill={C.peauFonce} />
        {[[170, 226], [194, 214], [220, 216], [244, 228], [186, 244], [214, 246], [238, 244], [160, 240]].map(([x, y]) => (
          <circle key={x + "-" + y} cx={x} cy={y} r="22" fill={C.sable} />
        ))}
        <ellipse cx="140" cy="236" rx="16" ry="22" fill={C.peauFonce} transform="rotate(28 140 236)" />
        <path d="M150 220 q14 -10 8 10 q-4 8 -10 2" fill="none" stroke={C.soleilFonce} strokeWidth="5" strokeLinecap="round" />
        <circle cx="134" cy="232" r="3" fill={C.blanc} />
      </g>
      {[[100, 288], [250, 300], [330, 292]].map(([x, y]) => (
        <path key={x} d={`M${x} ${y} l4 -12 l4 12 l4 -10 l4 10`} fill="none" stroke={C.baobab} strokeWidth="3" strokeLinejoin="round" />
      ))}
    </Cadre>
  );
}
