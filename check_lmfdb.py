#!/usr/bin/env python3
"""
Check detailed LMFDB data for galmap 7T6-4.2.1_3.2.2_3.2.2-a
"""

from lmf import db

def check_galmap_details():
    galmap_label = "7T6-4.2.1_3.2.2_3.2.2-a"
    
    print(f"Checking galmap: {galmap_label}")
    print("=" * 50)
    
    # Get galmap data
    galmaps = list(db.belyi_galmaps.search({"label": galmap_label}))
    print(f"Found {len(galmaps)} galmap(s)")
    
    for galmap in galmaps:
        print(f"Galmap: {galmap['label']}")
        print(f"  Passport: {galmap['BelyiDB_plabel']}")
        print(f"  Degree: {galmap.get('deg', 'N/A')}")
        print(f"  Genus: {galmap.get('g', 'N/A')}")
        print(f"  Geometric Type: {galmap.get('geomtype', 'N/A')}")
        print(f"  Orbit Size: {galmap.get('orbit_size', 'N/A')}")
        print(f"  Triples: {galmap['triples_cyc']}")
        print(f"  All fields: {list(galmap.keys())}")
        print()

if __name__ == "__main__":
    check_galmap_details() 