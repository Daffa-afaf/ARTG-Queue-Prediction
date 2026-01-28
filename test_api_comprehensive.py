import pandas as pd

df = pd.read_csv('Data/processed/dataset_final2bulan_42FEATURES_PROPER.csv')

# Filter tepat 40.53 menit
exact_40_53 = df[df['GATE_IN_STACK'] == 40.53]

print("="*60)
print("ANALYSIS: 8 RECORDS WITH EXACTLY 40.53 MINUTES")
print("="*60)

print(f"\nTotal records: {len(exact_40_53)}")

# Tampilkan semua 8 record
print("\nAll 8 records:")
print(exact_40_53[['slot', 'tier', 'block', 'CONTAINER_SIZE', 'CTR_STATUS', 
                   'CONTAINER_TYPE', 'JOB_TYPE', 'gate_in_hour', 'GATE_IN_STACK']])

# Kelompokkan berdasarkan karakteristik
print(f"\n{'='*60}")
print("PATTERNS IN 40.53 MIN CASES")
print("="*60)

print("\nBy Slot:")
print(exact_40_53['slot'].value_counts())

print("\nBy Tier:")
print(exact_40_53['tier'].value_counts())

print("\nBy Block:")
print(exact_40_53['block'].value_counts())

print("\nBy Container Size:")
print(exact_40_53['CONTAINER_SIZE'].value_counts())

print("\nBy Status:")
print(exact_40_53['CTR_STATUS'].value_counts())

print("\nBy Hour:")
print(exact_40_53['gate_in_hour'].value_counts())

# Periksa apakah ada pola umum
print(f"\n{'='*60}")
print("HYPOTHESIS CHECK")
print("="*60)

# Periksa apakah window waktu yang sama
hours = exact_40_53['gate_in_hour'].unique()
print(f"\nUnique hours: {sorted(hours)}")

# Check if same day
if 'gate_in_day' in exact_40_53.columns:
    days = exact_40_53['gate_in_day'].unique()
    print(f"Unique days: {sorted(days)}")

print("\n💡 POSSIBLE EXPLANATIONS:")
if len(exact_40_53['gate_in_hour'].unique()) == 1:
    print("   ✅ All 8 trucks processed at SAME HOUR")
    print("   → Likely: Operational incident at specific time")
    print("   → Equipment breakdown, shift change delay, etc.")
elif len(exact_40_53['slot'].unique()) == 1:
    print("   ✅ All 8 trucks at SAME SLOT")
    print("   → Likely: Slot-specific issue (blocking, access)")
else:
    print("   ⚠️  Different slots, tiers, and times")
    print("   → Possible: System-wide issue affecting all operations")
    print("   → Or: Coincidence (rare but possible)")
