"""Planificateur : génère les rappels de remboursement chaque jour à 07 h 00 (heure de Dakar).

Usage :
    python -m app.planificateur              # processus à laisser tourner
    python -m app.planificateur --maintenant # génère une première fois tout de suite
"""
import argparse
import logging
from datetime import date

from apscheduler.schedulers.blocking import BlockingScheduler

from app.rappels import executer

HEURE, MINUTE = 7, 0

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")


def tache() -> None:
    crees = executer(date.today())
    logging.info("Rappels générés : %d %s", sum(crees.values()), crees)


def main() -> None:
    parseur = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parseur.add_argument("--maintenant", action="store_true")
    args = parseur.parse_args()

    if args.maintenant:
        tache()

    planificateur = BlockingScheduler(timezone="Africa/Dakar")
    # coalesce : si plusieurs exécutions ont été manquées, une seule est rejouée.
    # misfire_grace_time : une exécution peut avoir jusqu'à 1 h de retard (ordinateur en veille).
    planificateur.add_job(tache, "cron", hour=HEURE, minute=MINUTE,
                          coalesce=True, misfire_grace_time=3600)
    logging.info("Planificateur démarré : rappels chaque jour à %02d h %02d (Dakar)", HEURE, MINUTE)
    planificateur.start()


if __name__ == "__main__":
    main()
