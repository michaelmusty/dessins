#!/usr/bin/env python3
"""
Check actual LMFDB data for available passports
"""

from lmf import db

def check_available_passports():
    print("Checking available passports in LMFDB...")
    print("=" * 50)
    
    # Get some sample passports
    passports = list(db.belyi_passports.search({}, limit=10))
    print(f"Found {len(passports)} sample passports:")
    
    for passport in passports:
        print(f"  {passport['BelyiDB_plabel']}")
    
    print("\n" + "=" * 50)
    
    # Check for 7T6 passports specifically
    print("Checking for 7T6 passports...")
    t6_passports = list(db.belyi_passports.search({"group": "7T6"}, limit=5))
    print(f"Found {len(t6_passports)} 7T6 passports:")
    
    for passport in t6_passports:
        print(f"  {passport['BelyiDB_plabel']}")
        # Get galmaps for this passport
        galmaps = list(db.belyi_galmaps.search({"BelyiDB_plabel": passport['BelyiDB_plabel']}))
        print(f"    Has {len(galmaps)} galmap(s)")
        for galmap in galmaps:
            print(f"      - {galmap['label']}")
        print()

if __name__ == "__main__":
    check_available_passports() 