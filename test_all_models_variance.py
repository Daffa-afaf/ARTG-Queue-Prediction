import pandas as pd

df = pd.read_csv('Data/processed/dataset_final2bulan_42FEATURES_PROPER.csv')

print("="*60)
print("SLOT ANALYSIS")
print("="*60)

# Check slot type
print(f"Slot dtype: {df['slot'].dtype}")

# Check unique slots
unique_slots = sorted(df['slot'].unique())
print(f"\nTotal unique slots: {len(unique_slots)}")
print(f"\nAll unique slots:")
print(unique_slots)

# Check if 21 or '21' exists
has_21_float = 21.0 in df['slot'].values or 21 in df['slot'].values
has_21_string = '21' in df['slot'].values

print(f"\nSlot 21 as float/int: {'YES ✅' if has_21_float else 'NO ❌'}")
print(f"Slot '21' as string: {'YES ✅' if has_21_string else 'NO ❌'}")

# If has 21, show count
if has_21_float:
    count = len(df[df['slot'] == 21])
    print(f"Count: {count}")
    
if has_21_string:
    count = len(df[df['slot'] == '21'])
    print(f"Count: {count}")

# Check slot range
print(f"\nSlot range:")
print(f"   Min: {df['slot'].min()}")
print(f"   Max: {df['slot'].max()}")