// Logo : une pousse en forme de « Y » (Yokkuté = progrès, en wolof).
// La tige et la feuille gauche portent la croissance, la feuille dorée évoque le crédit qui fait grandir.
// Aplats uniquement. "clair" : version pour les fonds sombres.
export default function LogoMarque({ clair = false, className = "h-9 w-9" }) {
  const fond = clair ? "#ffffff" : "#2d3db3";
  const motif = clair ? "#2d3db3" : "#ffffff";
  return (
    <svg viewBox="0 0 40 40" className={className} aria-hidden="true" xmlns="http://www.w3.org/2000/svg">
      <rect width="40" height="40" rx="12" fill={fond} />
      <path d="M20 31.5 V19" fill="none" stroke={motif} strokeWidth="3.6" strokeLinecap="round" />
      <path d="M19.6 21.5 C19.6 14.6 15 10.2 8.6 10.2 C8.6 17.1 13.2 21.5 19.6 21.5 Z" fill={motif} />
      <path d="M20.4 18.3 C20.4 11.4 25 7 31.4 7 C31.4 13.9 26.8 18.3 20.4 18.3 Z" fill="#f5b70a" />
    </svg>
  );
}
