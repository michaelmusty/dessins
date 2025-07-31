#!/usr/bin/env python3
"""
Check actual permutation triples for galmaps from LMFDB
"""

from lmf import db

def check_galmap_triples():
    galmaps_to_check = [
        "5T3-4.1_4.1_2.2.1-a",
        "6T16-3.2.1_3.2.1_3.3-a"
    ]
    
    for galmap_label in galmaps_to_check:
        print(f"Checking galmap: {galmap_label}")
        print("=" * 60)
        
        # Get galmap data
        galmaps = list(db.belyi_galmaps.search({"label": galmap_label}))
        print(f"Found {len(galmaps)} galmap(s)")
        
        for galmap in galmaps:
            print(f"Galmap: {galmap['label']}")
            print(f"  Passport: {galmap['BelyiDB_plabel']}")
            print(f"  Degree: {galmap.get('deg', 'N/A')}")
            print(f"  Orbit Size: {galmap.get('orbit_size', 'N/A')}")
            print(f"  Triples (cycle): {galmap['triples_cyc']}")
            print()
            
            # Show each triple separately
            for i, triple in enumerate(galmap['triples_cyc']):
                print(f"  Triple {i+1}:")
                print(f"    σ₀ = {triple[0]}")
                print(f"    σ₁ = {triple[1]}")
                print(f"    σ∞ = {triple[2]}")
                print()
        
        print("\n" + "="*60 + "\n")

if __name__ == "__main__":
    check_galmap_triples() 