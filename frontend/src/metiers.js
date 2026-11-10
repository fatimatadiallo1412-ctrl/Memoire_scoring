import { useEffect, useState } from "react";
import { appeler } from "./api";

let cache = null;

export function invaliderMetiers() {
  cache = null;
}

export function useMetiers() {
  const [metiers, setMetiers] = useState(cache || []);
  useEffect(() => {
    if (cache) return;
    appeler("/professions")
      .then((liste) => {
        cache = liste;
        setMetiers(liste);
      })
      .catch(() => {});
  }, []);
  return metiers;
}
