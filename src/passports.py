"""
A Passport class to construct a passport from an lmfdb passport
"""

from src.galois_orbits import GaloisOrbit


class Passport:
    def __init__(self, passport: dict):
        self.passport = passport
    
    def __str__(self):
        return f"Passport(passport={self.passport})"

    @classmethod
    def from_galois_orbit(cls, galois_orbit: GaloisOrbit):
        return cls(galois_orbit.to_passport())
    