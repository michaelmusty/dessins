
"""
time pdm run vis.py
"""

from lmf import db
from loguru import logger
from src.dessins import Dessin
from src.galois_orbits import GaloisOrbit

def main():
    galmap = list(db.belyi_galmaps.search({"label": "7T5-7_2.2.1.1.1_3.3.1-a"}))
    assert len(galmap) == 1
    galois_orbit = GaloisOrbit(galmap[0])
    triples = galois_orbit.get_triples_cyc()
    for i,t in enumerate(triples):
        logger.info(f"{galois_orbit.get_passport_label()}: {i} {t}")
        dessin = Dessin(t, galois_orbit)
        dessin.to_json(i)

if __name__ == "__main__":
    main()
