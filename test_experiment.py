import pandas as pd

df = pd.read_csv('Data/processed/dataset_final2bulan_42FEATURES_PROPER.csv')

print("="*60)
print("O/T (OPEN TOP) CONTAINER ANALYSIS")
print("="*60)

# Filter O/T containers
ot_containers = df[df['CONTAINER_TYPE'].str.contains('O/T|OPEN|FLT', case=False, na=False)]

print(f"\nTotal O/T containers: {len(ot_containers)}")
print(f"Mean duration: {ot_containers['GATE_IN_STACK'].mean():.2f} min")
print(f"Median duration: {ot_containers['GATE_IN_STACK'].median():.2f} min")
print(f"Std deviation: {ot_containers['GATE_IN_STACK'].std():.2f} min")

print(f"\n{'='*60}")
print("O/T CONTAINERS BY STATUS")
print("="*60)

# O/T FCL (Full)
ot_fcl = ot_containers[ot_containers['CTR_STATUS'] == 'FCL']
print(f"\nO/T FCL (Full):")
print(f"   Count: {len(ot_fcl)}")
print(f"   Mean: {ot_fcl['GATE_IN_STACK'].mean():.2f} min")

# O/T MTY (Empty)
ot_mty = ot_containers[ot_containers['CTR_STATUS'] == 'MTY']
print(f"\nO/T MTY (Empty):")
print(f"   Count: {len(ot_mty)}")
print(f"   Mean: {ot_mty['GATE_IN_STACK'].mean():.2f} min")

if len(ot_mty) > 0:
    print(f"   Median: {ot_mty['GATE_IN_STACK'].median():.2f} min")
    print(f"   Min: {ot_mty['GATE_IN_STACK'].min():.2f} min")
    print(f"   Max: {ot_mty['GATE_IN_STACK'].max():.2f} min")
    
    # Distribution
    print(f"\n   Duration Distribution:")
    print(f"      < 15 min:  {len(ot_mty[ot_mty['GATE_IN_STACK'] < 15])} ({len(ot_mty[ot_mty['GATE_IN_STACK'] < 15])/len(ot_mty)*100:.1f}%)")
    print(f"      15-30 min: {len(ot_mty[(ot_mty['GATE_IN_STACK'] >= 15) & (ot_mty['GATE_IN_STACK'] < 30)])} ({len(ot_mty[(ot_mty['GATE_IN_STACK'] >= 15) & (ot_mty['GATE_IN_STACK'] < 30)])/len(ot_mty)*100:.1f}%)")
    print(f"      > 30 min:  {len(ot_mty[ot_mty['GATE_IN_STACK'] >= 30])} ({len(ot_mty[ot_mty['GATE_IN_STACK'] >= 30])/len(ot_mty)*100:.1f}%)")

print(f"\n{'='*60}")
print("COMPARISON: O/T vs DRY CONTAINERS")
print("="*60)

# DRY MTY for comparison
dry_mty = df[(df['CONTAINER_TYPE'] == 'DRY') & (df['CTR_STATUS'] == 'MTY')]

print(f"\nDRY MTY (Empty):")
print(f"   Count: {len(dry_mty)}")
print(f"   Mean: {dry_mty['GATE_IN_STACK'].mean():.2f} min")

if len(ot_mty) > 0:
    diff = ot_mty['GATE_IN_STACK'].mean() - dry_mty['GATE_IN_STACK'].mean()
    print(f"\nO/T MTY vs DRY MTY:")
    print(f"   Difference: {diff:.2f} min")
    if diff > 5:
        print(f"   ⚠️  O/T MTY is significantly SLOWER than DRY MTY!")
        print(f"   → Model learns: O/T = slow (even when empty)")
    elif diff < -2:
        print(f"   ✅ O/T MTY is actually FASTER than DRY MTY")
    else:
        print(f"   → Similar processing time")

# Check 20ft MTY O/T specifically
ft20_mty_ot = df[(df['CONTAINER_SIZE'] == 20) & 
                  (df['CTR_STATUS'] == 'MTY') & 
                  (df['CONTAINER_TYPE'].str.contains('O/T|OPEN', case=False, na=False))]

print(f"\n{'='*60}")
print("SPECIFIC: 20FT MTY O/T (Matching H9466OV)")
print("="*60)

if len(ft20_mty_ot) > 0:
    print(f"\nTotal cases: {len(ft20_mty_ot)}")
    print(f"Mean: {ft20_mty_ot['GATE_IN_STACK'].mean():.2f} min")
    print(f"Median: {ft20_mty_ot['GATE_IN_STACK'].median():.2f} min")
    print(f"Std: {ft20_mty_ot['GATE_IN_STACK'].std():.2f} min")
    print(f"Min: {ft20_mty_ot['GATE_IN_STACK'].min():.2f} min")
    print(f"Max: {ft20_mty_ot['GATE_IN_STACK'].max():.2f} min")
    
    print(f"\n💡 CONCLUSION:")
    print(f"   Model predicted: 42.40 min")
    print(f"   Actual (H9466OV): 10.48 min")
    print(f"   Typical for 20ft MTY O/T: {ft20_mty_ot['GATE_IN_STACK'].mean():.0f} min")
    
    if ft20_mty_ot['GATE_IN_STACK'].mean() > 30:
        print(f"\n   ⚠️  20ft MTY O/T historically SLOW!")
        print(f"   Model prediction is based on historical average")
        print(f"   H9466OV case (10 min) is ANOMALY - unusually fast!")
    elif ft20_mty_ot['GATE_IN_STACK'].mean() < 15:
        print(f"\n   ✅ 20ft MTY O/T should be FAST!")
        print(f"   Model OVERESTIMATE severely - investigation needed")
else:
    print(f"\n⚠️  NO training data for 20ft MTY O/T!")
    print(f"   Model has never seen this combination")
    print(f"   Prediction based on similar containers (O/T general average)")
    print(f"\n   This explains the overestimate:")
    print(f"   - Model sees O/T (usually slow when full)")
    print(f"   - Model doesn't know O/T MTY behavior")
    print(f"   - Predicts conservatively high")
