import { useEffect, useRef, useState } from "react";

// Fait apparaître doucement un bloc quand il entre dans l'écran (une seule fois).
// Sans IntersectionObserver ou avec « réduire les animations », le bloc est visible d'emblée.
export default function Revele({ as: Balise = "div", delai = 0, className = "", children }) {
  const ref = useRef(null);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const el = ref.current;
    const reduit = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (!el || reduit || !("IntersectionObserver" in window)) {
      setVisible(true);
      return undefined;
    }
    const observateur = new IntersectionObserver(
      ([entree]) => {
        if (entree.isIntersecting) {
          setVisible(true);
          observateur.disconnect();
        }
      },
      { threshold: 0.15, rootMargin: "0px 0px -40px 0px" },
    );
    observateur.observe(el);
    return () => observateur.disconnect();
  }, []);

  return (
    <Balise
      ref={ref}
      style={{ transitionDelay: visible ? delai + "ms" : "0ms" }}
      className={
        "transition duration-700 ease-out " +
        (visible ? "translate-y-0 opacity-100" : "translate-y-6 opacity-0") +
        (className ? " " + className : "")
      }
    >
      {children}
    </Balise>
  );
}
