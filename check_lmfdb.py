#!/usr/bin/env python3
"""
Get all genus zero passports up to degree 6 from LMFDB
"""

from lmf import db

def get_genus_zero_passports():
    print("Getting genus zero passports up to degree 6...")
    print("=" * 60)
    
    # Get all genus zero passports up to degree 6
    passports = list(db.belyi_passports.search({"g": 0, "deg": {"$lte": 6}}, limit=50))
    print(f"Found {len(passports)} genus zero passports up to degree 6:")
    
    for passport in passports:
        print(f"  {passport['BelyiDB_plabel']} (degree {passport['deg']}, {passport.get('num_orbits', 'N/A')} orbits)")
        
        # Get galmaps for this passport
        galmaps = list(db.belyi_galmaps.search({"BelyiDB_plabel": passport['BelyiDB_plabel']}))
        print(f"    Has {len(galmaps)} galmap(s)")
        for galmap in galmaps:
            print(f"      - {galmap['label']} (orbit size: {galmap.get('orbit_size', 'N/A')})")
        print()

if __name__ == "__main__":
    get_genus_zero_passports() 