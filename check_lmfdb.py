#!/usr/bin/env python3
"""
Check actual permutation triples for galmaps from LMFDB
"""

from lmf import db

# Check a specific passport to see its data structure
passport = list(db.belyi_passports.search({"BelyiDB_plabel": "3T1-[3,3,1]-3-3-111-g0"}))[0]
print("Passport data structure:")
for key, value in passport.items():
    print(f"  {key}: {value}")

print("\n" + "="*50)

# Check what the correct LMFDB URL should be
print("Available fields that might be used for LMFDB URLs:")
for key in passport.keys():
    if 'label' in key.lower() or 'url' in key.lower():
        print(f"  {key}: {passport[key]}") 