// Règles de format communes (identiques à app/validation.py côté API).

// Mobile sénégalais : 9 chiffres commençant par 70, 71, 75, 76, 77 ou 78 (espaces tolérés à la saisie).
export const TELEPHONE = {
  pattern: "\\s*7[015678](\\s?[0-9]){7}\\s*",
  title: "9 chiffres commençant par 70, 71, 75, 76, 77 ou 78 (ex. 77 123 45 67)",
  placeholder: "77 123 45 67",
  inputMode: "numeric",
};
export const AIDE_TELEPHONE = "9 chiffres commençant par 70, 71, 75, 76, 77 ou 78.";

// Adresse Gmail uniquement (majuscules acceptées, l'API enregistre en minuscules).
export const GMAIL = {
  pattern: "\\s*[A-Za-z0-9._%+\\-]+@[Gg][Mm][Aa][Ii][Ll]\\.[Cc][Oo][Mm]\\s*",
  title: "Une adresse se terminant par @gmail.com",
  placeholder: "prenom.nom@gmail.com",
};
export const AIDE_GMAIL = "Adresse @gmail.com uniquement.";
