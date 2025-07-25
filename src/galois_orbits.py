"""
A GaloisOrbit class to construct a Galois orbit of Belyi maps from an lmfdb galmap
"""

from lmf import db

class GaloisOrbit:
    def __init__(self, galmap: dict):
        self.galmap = galmap
    
    def __str__(self):
        return f"GaloisOrbit(galmap={self.galmap})"
    
    def __repr__(self):
        return self.__str__()
    
    def __eq__(self, other):
        return self.galmap == other.galmap

    def get_triples(self):
        return self.galmap["triples"]

    def get_triples_cyc(self):
        return self.galmap["triples_cyc"]

    def get_passport_label(self):
        return self.galmap["BelyiDB_plabel"]

    def get_label(self):
        return self.galmap["label"]

    def get_BelyiDB_label(self):
        return self.galmap["BelyiDB_label"]

    def to_passport(self):
        from src.passports import Passport
        passports = list(db.belyi_passports.search({"BelyiDB_plabel": self.galmap["BelyiDB_plabel"]}))
        if len(passports) != 1:
            raise ValueError(f"Expected 1 passport, got {len(passports)} for {self.galmap['BelyiDB_plabel']}")
        return Passport(passports[0])