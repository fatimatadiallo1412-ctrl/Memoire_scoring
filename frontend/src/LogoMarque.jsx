// Logo : une personne les bras levés (le client qui avance), dont un bras porte une pièce.
// Aplats uniquement. "clair" : version blanche pour les fonds bleus.
export default function LogoMarque({ clair = false, className = "h-9 w-9" }) {
  const fond = clair ? "#ffffff" : "#1f4e79";
  const trait = clair ? "#1f4e79" : "#ffffff";
  return (
    <svg viewBox="0 0 40 40" className={className} aria-hidden="true" xmlns="http://www.w3.org/2000/svg">
      <rect width="40" height="40" rx="10" fill={fond} />
      <path d="M11 11 L20 21 L29 11 M20 21 V31" fill="none" stroke={trait} strokeWidth="4.5"
        strokeLinecap="round" strokeLinejoin="round" />
      <circle cx="30" cy="9.5" r="3.4" fill="#f2b705" />
    </svg>
  );
}
