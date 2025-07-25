"""
time pdm run happy.py
"""

from lmf import db
from loguru import logger
from src.dessins import Dessin
from src.galois_orbits import GaloisOrbit
from src.passports import Passport

def main():
    for d in [1,2,3,4,5,6,7,8,9]:
        passports = list(db.belyi_passports.search({"deg": d}))
        logger.info(f"deg {d}: {len(passports)} passports\n")
        for p in passports:
            passport = Passport(p)
            logger.info(passport)
            galmaps = list(db.belyi_galmaps.search({"BelyiDB_plabel": p["BelyiDB_plabel"]}))
            logger.info(f"{p['BelyiDB_plabel']}: {len(galmaps)} galmaps")
            for g in galmaps:
                logger.info(g["BelyiDB_label"])
                galois_orbit = GaloisOrbit(g)
                logger.info(galois_orbit.get_triples())
                logger.info(galois_orbit.get_triples_cyc())
                logger.info(galois_orbit.get_passport_label())
                logger.info(galois_orbit.to_passport())
                for t in galois_orbit.get_triples_cyc():
                    dessin = Dessin(t, galois_orbit)
                    logger.info(dessin)
                    logger.info(dessin.to_networkx_graph())
                    logger.info(dessin.adjacency_matrix())
                    logger.info(dessin.is_planar())

            logger.info("\n")

if __name__ == "__main__":
    main()
