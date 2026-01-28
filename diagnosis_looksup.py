"""
DIAGNOSTIC SCRIPT - Check Lookup Tables
========================================
Run this to verify lookup tables are working correctly
"""

import joblib
import pandas as pd

print("=" * 80)
print("LOOKUP TABLES DIAGNOSTIC")
print("=" * 80)

# Load lookup tables
try:
    lookup_tables = joblib.load('models/lookup_tables.pkl')
    print("\n✅ Lookup tables loaded successfully!")
except Exception as e:
    print(f"\n❌ Error loading lookup tables: {e}")
    exit(1)

# Check global stats
global_stats = lookup_tables.get('global_stats', {})
print(f"\n📊 Global Statistics:")
print(f"   Mean: {global_stats.get('mean', 0):.2f} minutes")

# Test specific lookups
print("\n" + "=" * 80)
print("TESTING LOOKUPS WITH SAMPLE DATA")
print("=" * 80)

# Test Case 1: Common slot
test_slot = '14'
slot_avg = lookup_tables.get('slot_avg', {}).get(test_slot, None)
print(f"\n1. Slot '{test_slot}':")
print(f"   Historical avg: {slot_avg:.2f} min" if slot_avg else "   ❌ NOT FOUND!")

# Test Case 2: Common block
test_block = '1F'
block_target = lookup_tables.get('block_target', {}).get(test_block, None)
print(f"\n2. Block '{test_block}':")
print(f"   Target encoding: {block_target:.2f} min" if block_target else "   ❌ NOT FOUND!")

# Test Case 3: Location with space format
test_location_space = '14 02 2'
lokasi_avg_space = lookup_tables.get('lokasi_avg', {}).get(test_location_space, None)
print(f"\n3. Location '{test_location_space}' (space format):")
print(f"   Historical avg: {lokasi_avg_space:.2f} min" if lokasi_avg_space else "   ❌ NOT FOUND!")

# Test Case 4: Location with underscore format
test_location_underscore = '14_02_2'
lokasi_avg_underscore = lookup_tables.get('lokasi_avg', {}).get(test_location_underscore, None)
print(f"\n4. Location '{test_location_underscore}' (underscore format):")
print(f"   Historical avg: {lokasi_avg_underscore:.2f} min" if lokasi_avg_underscore else "   ❌ NOT FOUND!")

# Check available keys
print("\n" + "=" * 80)
print("AVAILABLE KEYS SAMPLE")
print("=" * 80)

print(f"\n📊 Slot keys (first 10):")
slot_keys = list(lookup_tables.get('slot_avg', {}).keys())[:10]
print(f"   {slot_keys}")

print(f"\n📊 Block keys (all):")
block_keys = list(lookup_tables.get('block_target', {}).keys())
print(f"   {block_keys}")

print(f"\n📊 Location keys (first 10):")
lokasi_keys = list(lookup_tables.get('lokasi_avg', {}).keys())[:10]
print(f"   {lokasi_keys}")

# Check format consistency
print("\n" + "=" * 80)
print("KEY FORMAT CHECK")
print("=" * 80)

has_space_in_blocks = any(' ' in str(k) for k in block_keys)
has_space_in_lokasi = any(' ' in str(k) and '_' not in str(k) for k in lokasi_keys[:10])
has_underscore_in_lokasi = any('_' in str(k) for k in lokasi_keys[:10])

print(f"\n📝 Block keys have trailing spaces: {'❌ YES (BAD!)' if has_space_in_blocks else '✅ NO'}")
print(f"📝 Location uses space format: {'✅ YES' if has_space_in_lokasi else '❌ NO'}")
print(f"📝 Location uses underscore format: {'✅ YES' if has_underscore_in_lokasi else '❌ NO'}")

# DIAGNOSIS
print("\n" + "=" * 80)
print("DIAGNOSIS")
print("=" * 80)

issues = []

if slot_avg is None:
    issues.append("❌ Slot lookup failed - keys may not match!")

if block_target is None:
    issues.append("❌ Block lookup failed - keys may not match!")

if lokasi_avg_space is None and lokasi_avg_underscore is None:
    issues.append("❌ Location lookup failed - format mismatch!")

if has_space_in_blocks:
    issues.append("❌ Block keys have trailing spaces!")

if lokasi_avg_space and not lokasi_avg_underscore:
    issues.append("⚠️  Location uses SPACE format, but App.py expects UNDERSCORE!")
elif lokasi_avg_underscore and not lokasi_avg_space:
    issues.append("⚠️  Location uses UNDERSCORE format, App.py may send SPACE!")

if issues:
    print("\n❌ ISSUES FOUND:")
    for issue in issues:
        print(f"   {issue}")
    print("\n💡 SOLUTION: Regenerate lookup tables or fix App.py key format!")
else:
    print("\n✅ All lookups working correctly!")

print("=" * 80)