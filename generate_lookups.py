"""
GENERATE LOOKUP TABLES FOR PRODUCTION
=======================================
Script ini generate lookup tables untuk historical features, congestion patterns,
dan target encoding yang akan dipakai di production (Flask API).

CRITICAL: Lookup tables HARUS di-generate dari DATASET YANG SAMA dengan yang dipakai training!

Input:  Data/processed/dataset_final2bulan_42FEATURES_PROPER.csv
Output: models/lookup_tables_2bulan.pkl (semua lookup tables dalam 1 file)
"""

import pandas as pd
import numpy as np
import joblib
from datetime import datetime
import os
import sys

print("="*80)
print("GENERATE LOOKUP TABLES FOR PRODUCTION")
print("="*80)
print(f"Started at: {datetime.now()}")
print(f"Current directory: {os.getcwd()}")
print()

# ============================================================================
# 1. MUAT DATASET (YANG SAMA DENGAN TRAINING!)
# ============================================================================
print("1. Loading dataset...")

# Path untuk struktur Project1-Magang
dataset_path = 'Data/processed/dataset_final2bulan_42FEATURES_PROPER.csv'

if not os.path.exists(dataset_path):
    print(f"❌ ERROR: Dataset file not found at: {dataset_path}")
    print(f"   Full path: {os.path.abspath(dataset_path)}")
    print("\nPlease ensure:")
    print("   1. You are running this script from: D:\\Project1-Magang\\")
    print("   2. Dataset exists at: D:\\Project1-Magang\\Data\\processed\\dataset_final2bulan_42FEATURES_PROPER.csv")
    sys.exit(1)

df = pd.read_csv(dataset_path)

print(f"   ✅ Dataset loaded: {len(df):,} records")
print(f"   Full path: {os.path.abspath(dataset_path)}")
print()

# ============================================================================
# 2. SIAPKAN FITUR LOKASI
# ============================================================================
print("2. Preparing location features...")

# Ekstrak versi numerik untuk agregasi
def clean_categorical_value(value):
    """Bersihkan nilai kategorikal - sama seperti training"""
    s = str(value).strip()
    if s.endswith('.0'):
        s = s[:-2]
    return s

# Bersihkan kolom kategorikal
df['slot'] = df['slot'].apply(clean_categorical_value)
df['tier'] = df['tier'].apply(clean_categorical_value)
df['block'] = df['block'].apply(clean_categorical_value)
df['gate_in_shift'] = df['gate_in_shift'].apply(clean_categorical_value)

# Versi numerik untuk pengelompokan
df['slot_numeric'] = pd.to_numeric(df['slot'], errors='coerce').fillna(0).astype(int)
df['tier_numeric'] = pd.to_numeric(df['tier'], errors='coerce').fillna(0).astype(int)

# Buat kolom LOKASI (gabungan slot + row + tier)
# Catatan: Dataset 2 bulan tidak punya kolom ROW terpisah, tapi punya row_numeric
if 'row_numeric' in df.columns:
    df['LOKASI'] = df['slot'] + ' ' + df['row_numeric'].astype(str) + ' ' + df['tier']
else:
    # Fallback: gunakan slot dan tier saja
    df['LOKASI'] = df['slot'] + ' ' + df['tier']

print(f"   ✅ Location features prepared")
print(f"   Unique slots: {df['slot'].nunique()}")
print(f"   Unique tiers: {df['tier'].nunique()}")
print(f"   Unique blocks: {df['block'].nunique()}")
print(f"   Unique LOKASI: {df['LOKASI'].nunique()}")
print()

# ============================================================================
# 3. GENERATE RATA-RATA HISTORIS
# ============================================================================
print("3. Generating historical averages...")

lookup_tables = {}

# Rata-rata historis slot
slot_avg = df.groupby('slot')['GATE_IN_STACK'].mean().to_dict()
lookup_tables['slot_historical_avg'] = slot_avg
print(f"   ✅ Slot historical avg: {len(slot_avg)} entries")

# Rata-rata historis tier
tier_avg = df.groupby('tier')['GATE_IN_STACK'].mean().to_dict()
lookup_tables['tier_historical_avg'] = tier_avg
print(f"   ✅ Tier historical avg: {len(tier_avg)} entries")

# Rata-rata historis LOKASI
lokasi_avg = df.groupby('LOKASI')['GATE_IN_STACK'].mean().to_dict()
lookup_tables['lokasi_historical_avg'] = lokasi_avg
print(f"   ✅ LOKASI historical avg: {len(lokasi_avg)} entries")

# Rata-rata historis jam (0-23)
hour_avg = df.groupby('gate_in_hour')['GATE_IN_STACK'].mean().to_dict()
lookup_tables['hour_historical_avg'] = hour_avg
print(f"   ✅ Hour historical avg: {len(hour_avg)} entries")

# Rata-rata keseluruhan (fallback)
overall_avg = df['GATE_IN_STACK'].mean()
lookup_tables['overall_avg'] = overall_avg
print(f"   ✅ Overall avg: {overall_avg:.2f} minutes")
print()

# ============================================================================
# 4. GENERATE TARGET ENCODING
# ============================================================================
print("4. Generating target encoding...")

# BLOCK target encoding
block_target_enc = df.groupby('block')['GATE_IN_STACK'].mean().to_dict()
lookup_tables['BLOCK_target_enc'] = block_target_enc
print(f"   ✅ BLOCK target encoding: {len(block_target_enc)} entries")

# LOKASI target encoding (sama dengan lokasi_historical_avg)
lookup_tables['LOKASI_target_enc'] = lokasi_avg
print(f"   ✅ LOKASI target encoding: {len(lokasi_avg)} entries")
print()

# ============================================================================
# 5. GENERATE LOOKUP FITUR STATISTIK
# ============================================================================
print("5. Generating statistical features lookups...")

# Statistik durasi slot
slot_std = df.groupby('slot')['GATE_IN_STACK'].std().fillna(0).to_dict()
slot_min = df.groupby('slot')['GATE_IN_STACK'].min().to_dict()
slot_max = df.groupby('slot')['GATE_IN_STACK'].max().to_dict()

lookup_tables['slot_duration_std'] = slot_std
lookup_tables['slot_duration_min'] = slot_min
lookup_tables['slot_duration_max'] = slot_max

print(f"   ✅ Slot duration std: {len(slot_std)} entries")
print(f"   ✅ Slot duration min: {len(slot_min)} entries")
print(f"   ✅ Slot duration max: {len(slot_max)} entries")
print()

# ============================================================================
# 6. GENERATE POLA KEPADATAN
# ============================================================================
print("6. Generating congestion patterns...")

# Volume per jam berdasarkan jam
hourly_volume = df.groupby('gate_in_hour').size().to_dict()
lookup_tables['hourly_volume'] = hourly_volume
print(f"   ✅ Hourly volume: {len(hourly_volume)} entries")

# Rata-rata kepadatan berdasarkan kombinasi jam-slot
df['hour_slot_key'] = df['gate_in_hour'].astype(str) + '_' + df['slot']
congestion_by_hour_slot = df.groupby('hour_slot_key').size().to_dict()
lookup_tables['congestion_by_hour_slot'] = congestion_by_hour_slot
print(f"   ✅ Congestion by hour-slot: {len(congestion_by_hour_slot)} entries")
print()

# ============================================================================
# 7. GENERATE LOOKUP FITUR LAG
# ============================================================================
print("7. Generating lag features lookups...")

# Untuk produksi, kita akan gunakan data historis terbaru per lokasi
# Kelompokkan berdasarkan LOKASI dan ambil nilai terakhir yang diketahui

# Last 3 durations per location
location_history = {}
for lokasi in df['LOKASI'].unique():
    lokasi_data = df[df['LOKASI'] == lokasi]['GATE_IN_STACK'].tail(3).tolist()
    if len(lokasi_data) > 0:
        location_history[lokasi] = {
            'last_duration': lokasi_data[-1] if len(lokasi_data) >= 1 else lokasi_avg.get(lokasi, overall_avg),
            'last_3_durations': lokasi_data,
            'rolling_mean_3': np.mean(lokasi_data) if len(lokasi_data) > 0 else lokasi_avg.get(lokasi, overall_avg)
        }

lookup_tables['location_history'] = location_history
print(f"   ✅ Location history: {len(location_history)} locations")
print()

# ============================================================================
# 8. METADATA
# ============================================================================
print("8. Adding metadata...")

lookup_tables['metadata'] = {
    'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    'dataset_size': len(df),
    'dataset_path': dataset_path,
    'num_lookups': len(lookup_tables) - 1,  # -1 for metadata itself
    'shift_type': '8_shifts_3hours',  # CRITICAL: 8 shifts, 3 hours each
    'shift_bins': [0, 3, 6, 9, 12, 15, 18, 21, 24],
    'shift_labels': ['shift_1', 'shift_2', 'shift_3', 'shift_4', 'shift_5', 'shift_6', 'shift_7', 'shift_8'],
    'target_mean': overall_avg,
    'target_std': df['GATE_IN_STACK'].std(),
    'target_min': df['GATE_IN_STACK'].min(),
    'target_max': df['GATE_IN_STACK'].max(),
}

print(f"   ✅ Metadata added")
print()

# ============================================================================
# 9. SIMPAN LOOKUP TABLES
# ============================================================================
print("9. Saving lookup tables...")

# Buat direktori models jika belum ada
model_dir = 'models'
if not os.path.exists(model_dir):
    os.makedirs(model_dir)
    print(f"   Created models directory: {os.path.abspath(model_dir)}")

output_path = os.path.join(model_dir, 'lookup_tables_2bulan.pkl')
joblib.dump(lookup_tables, output_path)

print(f"   ✅ Lookup tables saved to: {output_path}")
print(f"   Full path: {os.path.abspath(output_path)}")
print()

# ============================================================================
# 10. RINGKASAN
# ============================================================================
print("="*80)
print("LOOKUP TABLES GENERATED SUCCESSFULLY!")
print("="*80)
print(f"\n📊 Summary:")
print(f"   Total lookup tables: {len(lookup_tables) - 1}")  # -1 for metadata
print(f"   Dataset records: {len(df):,}")
print(f"   Output file: {output_path}")
print(f"\n📋 Lookup tables created:")
for key in sorted(lookup_tables.keys()):
    if key != 'metadata':
        if isinstance(lookup_tables[key], dict):
            print(f"   - {key:30s}: {len(lookup_tables[key]):5d} entries")
        else:
            print(f"   - {key:30s}: {lookup_tables[key]}")

print(f"\n⚙️ Shift configuration:")
print(f"   Type: {lookup_tables['metadata']['shift_type']}")
print(f"   Bins: {lookup_tables['metadata']['shift_bins']}")
print(f"   Labels: {lookup_tables['metadata']['shift_labels']}")

print(f"\n📈 Target statistics:")
print(f"   Mean: {lookup_tables['metadata']['target_mean']:.2f} minutes")
print(f"   Std:  {lookup_tables['metadata']['target_std']:.2f} minutes")
print(f"   Min:  {lookup_tables['metadata']['target_min']:.2f} minutes")
print(f"   Max:  {lookup_tables['metadata']['target_max']:.2f} minutes")

print(f"\nCompleted at: {datetime.now()}")
print("="*80)