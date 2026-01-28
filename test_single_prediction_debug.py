import pandas as pd
import numpy as np

df = pd.read_csv('Data/processed/dataset_final2bulan_42FEATURES_PROPER.csv')

# Filter slot 21 (dengan BENAR!)
slot21 = df[df['slot'] == 21.0]

print("="*60)
print("SLOT 21 DETAILED ANALYSIS")
print("="*60)

print(f"\nTotal cases: {len(slot21)}")
print(f"Mean duration: {slot21['GATE_IN_STACK'].mean():.2f} min")
print(f"Median duration: {slot21['GATE_IN_STACK'].median():.2f} min")
print(f"Std deviation: {slot21['GATE_IN_STACK'].std():.2f} min")
print(f"Min duration: {slot21['GATE_IN_STACK'].min():.2f} min")
print(f"Max duration: {slot21['GATE_IN_STACK'].max():.2f} min")

print(f"\nDuration Distribution:")
print(f"   < 15 min:  {len(slot21[slot21['GATE_IN_STACK'] < 15]):4,} ({len(slot21[slot21['GATE_IN_STACK'] < 15])/len(slot21)*100:5.1f}%)")
print(f"   15-30 min: {len(slot21[(slot21['GATE_IN_STACK'] >= 15) & (slot21['GATE_IN_STACK'] < 30)]):4,} ({len(slot21[(slot21['GATE_IN_STACK'] >= 15) & (slot21['GATE_IN_STACK'] < 30)])/len(slot21)*100:5.1f}%)")
print(f"   30-45 min: {len(slot21[(slot21['GATE_IN_STACK'] >= 30) & (slot21['GATE_IN_STACK'] < 45)]):4,} ({len(slot21[(slot21['GATE_IN_STACK'] >= 30) & (slot21['GATE_IN_STACK'] < 45)])/len(slot21)*100:5.1f}%)")
print(f"   45-60 min: {len(slot21[(slot21['GATE_IN_STACK'] >= 45) & (slot21['GATE_IN_STACK'] < 60)]):4,} ({len(slot21[(slot21['GATE_IN_STACK'] >= 45) & (slot21['GATE_IN_STACK'] < 60)])/len(slot21)*100:5.1f}%)")
print(f"   > 60 min:  {len(slot21[slot21['GATE_IN_STACK'] >= 60]):4,} ({len(slot21[slot21['GATE_IN_STACK'] >= 60])/len(slot21)*100:5.1f}%)")

# Extreme cases
slot21_extreme = slot21[slot21['GATE_IN_STACK'] > 60]

if len(slot21_extreme) > 0:
    print(f"\n🚨 EXTREME CASES (> 60 min):")
    print(f"   Count: {len(slot21_extreme)}")
    print(f"   Percentage: {len(slot21_extreme)/len(slot21)*100:.2f}%")
    print(f"\n   Details (top 10):")
    extreme_sorted = slot21_extreme.sort_values('GATE_IN_STACK', ascending=False)
    for idx, row in extreme_sorted.head(10).iterrows():
        print(f"      Truck: {row.get('TRUCK_ID', 'N/A'):12s} | Duration: {row['GATE_IN_STACK']:6.2f} min | "
              f"Tier: {int(row['tier'])} | Size: {int(row['CONTAINER_SIZE'])} | Status: {row['CTR_STATUS']}")
    
    # Check if B9959JJ is in the list
    if 'TRUCK_ID' in extreme_sorted.columns:
        b9959jj = slot21_extreme[slot21_extreme['TRUCK_ID'] == 'B9959JJ']
        if len(b9959jj) > 0:
            print(f"\n   ✅ FOUND: Truck B9959JJ in extreme cases!")
            print(f"      Duration: {b9959jj['GATE_IN_STACK'].iloc[0]:.2f} min")
        else:
            print(f"\n   ⚠️  Truck B9959JJ NOT in extreme cases (might be different truck ID)")

# Check slot 21 + tier 1
slot21_tier1 = df[(df['slot'] == 21.0) & (df['tier'] == 1.0)]

print(f"\n{'='*60}")
print("SLOT 21 + TIER 1 ANALYSIS (Matching B9959JJ)")
print("="*60)

print(f"\nTotal cases: {len(slot21_tier1)}")
if len(slot21_tier1) > 0:
    print(f"Mean duration: {slot21_tier1['GATE_IN_STACK'].mean():.2f} min")
    print(f"Median duration: {slot21_tier1['GATE_IN_STACK'].median():.2f} min")
    print(f"Std deviation: {slot21_tier1['GATE_IN_STACK'].std():.2f} min")
    print(f"Max duration: {slot21_tier1['GATE_IN_STACK'].max():.2f} min")
    
    slot21_tier1_extreme = slot21_tier1[slot21_tier1['GATE_IN_STACK'] > 60]
    print(f"\nCases > 60 min: {len(slot21_tier1_extreme)} ({len(slot21_tier1_extreme)/len(slot21_tier1)*100:.2f}%)")
    
    if len(slot21_tier1_extreme) > 0:
        print(f"\n🎯 CONCLUSION:")
        print(f"   For Slot 21 + Tier 1:")
        print(f"   - Typical duration: {slot21_tier1['GATE_IN_STACK'].mean():.0f} min")
        print(f"   - Extreme case: {slot21_tier1['GATE_IN_STACK'].max():.0f} min")
        print(f"   - Model predicted: 26 min (close to typical)")
        print(f"   - Actual (B9959JJ): 70 min")
        print(f"   - This is an OUTLIER for this slot-tier combination")