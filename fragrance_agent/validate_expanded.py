"""Quick validation of the expanded seed molecule database."""
import sys
sys.path.insert(0, ".")

from knowledge.seed_molecules import get_seed_molecules

mols = get_seed_molecules()
print(f"Total seed molecules: {len(mols)}")

# Count by odor family
families = {}
for m in mols:
    for f in m.get("odor_families", []):
        families[f] = families.get(f, 0) + 1

print("\nOdor family coverage:")
for f, c in sorted(families.items(), key=lambda x: -x[1]):
    print(f"  {f}: {c}")

# Count by volatility
vols = {}
for m in mols:
    v = m.get("volatility", "unknown")
    vols[v] = vols.get(v, 0) + 1
print("\nVolatility distribution:")
for v, c in sorted(vols.items(), key=lambda x: -x[1]):
    print(f"  {v}: {c}")

# Count with CAS numbers
with_cas = sum(1 for m in mols if m.get("cas") and m["cas"] != "N/A")
print(f"\nMolecules with CAS numbers: {with_cas}/{len(mols)}")

# Count naturals vs synthetics
naturals = sum(1 for m in mols if "Natural" in m.get("name", "") or "Oil" in m.get("name", "") or "Absolute" in m.get("name", "") or "Resinoid" in m.get("name", ""))
print(f"Natural extracts: ~{naturals}")
print(f"Synthetic/isolated: ~{len(mols) - naturals}")
