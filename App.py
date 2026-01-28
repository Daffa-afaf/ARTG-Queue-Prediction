from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import pandas as pd
import numpy as np
import joblib
from datetime import datetime
import traceback
import os
from collections import defaultdict
import logging
import threading
import time

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Logging dasar untuk debugging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# VARIABEL GLOBAL
# ============================================================================

# Struktur antrian: {block_id: [truck1, truck2, ...]}
QUEUES = defaultdict(list)

# Label nama blok
BLOCK_LABELS = {
    1: "CY1",
    2: "CY2", 
    3: "CY3",
    4: "CY4",
    5: "CY5",
    6: "CY6",
    7: "D1"
}

# Mapping stack (tier) ke block_id yang valid
# Stack/Tier dan Block harus match - CY D1 hanya accept stack D1
STACK_TO_BLOCK_MAPPING = {
    "1": 1,      # Stack 1 -> Block 1 (CY1)
    "2": 2,      # Stack 2 -> Block 2 (CY2)
    "3": 3,      # Stack 3 -> Block 3 (CY3)
    "4": 4,      # Stack 4 -> Block 4 (CY4)
    "5": 5,      # Stack 5 -> Block 5 (CY5)
    "6": 6,      # Stack 6 -> Block 6 (CY6)
    "D1": 7,     # Stack D1 -> Block 7 (D1)
}

# Validasi stack yang diizinkan untuk setiap block
# Block D1 HANYA menerima stack D1, bukan 7!
BLOCK_VALID_STACKS = {
    1: ["1"],           # CY1 hanya terima stack 1
    2: ["2"],           # CY2 hanya terima stack 2
    3: ["3"],           # CY3 hanya terima stack 3
    4: ["4"],           # CY4 hanya terima stack 4
    5: ["5"],           # CY5 hanya terima stack 5
    6: ["6"],           # CY6 hanya terima stack 6
    7: ["D1"],          # D1 HANYA terima stack D1, NOT 7!
}

# ============================================================================
# CACHE DEDUPLIKASI
# ============================================================================

# Melacak truk yang sudah diproses agar prediksi tidak dobel
# Kunci: "TRUCK_ID_GATE_IN_TIME", nilai: timestamp saat ditambahkan
processed_trucks_cache = {}
cache_lock = threading.Lock()
cleanup_thread = None
cache_initialized = False

def initialize_cache_cleanup():
    """Memulai thread pembersih cache (hanya sekali saat startup)"""
    global cleanup_thread, cache_initialized
    
    if cache_initialized:
        return
    
    def cleanup_cache():
        """Menghapus entri cache yang berusia lebih dari 60 detik"""
        logger.info("Cache cleanup thread started")
        while True:
            try:
                time.sleep(30)  # Jalan tiap 30 detik
                with cache_lock:
                    current_time = time.time()
                    expired_keys = [
                        key for key, timestamp in processed_trucks_cache.items()
                        if current_time - timestamp > 60  # TTL 60 detik
                    ]
                    for key in expired_keys:
                        del processed_trucks_cache[key]
                    if expired_keys:
                        logger.info(f"Cleaned {len(expired_keys)} expired entries | Cache size: {len(processed_trucks_cache)}")
            except Exception as e:
                logger.error(f"Cache cleanup error: {e}")
    
    cleanup_thread = threading.Thread(target=cleanup_cache, daemon=True)
    cleanup_thread.start()
    cache_initialized = True
    logger.info("Deduplication cache cleanup thread initialized")

print("="*80)
print("LOADING MODEL AND LOOKUP TABLES...")
print("="*80)

try:
    model_dir = 'models'
    
    # Muat file model
    model = joblib.load(os.path.join(model_dir, 'best_model_2_bulan.pkl'))
    print("[OK] Model loaded")
    
    label_encoders = joblib.load(os.path.join(model_dir, 'label_encoders_2_bulan.pkl'))
    print("[OK] Label encoders loaded")
    
    features_list = joblib.load(os.path.join(model_dir, 'features_list_2_bulan.pkl'))
    print("[OK] Features list loaded")
    
    lookup_tables = joblib.load(os.path.join(model_dir, 'lookup_tables_2bulan.pkl'))
    print("[OK] Lookup tables loaded")
    
    print(f"\nConfiguration:")
    print(f"   Total features: {len(features_list)}")
    print(f"   Shift type: {lookup_tables['metadata']['shift_type']}")
    print(f"   Target mean: {lookup_tables['metadata']['target_mean']:.2f} minutes")
    print("="*80)
    
except Exception as e:
    print(f"[ERROR] loading model/lookups: {e}")
    print("Please ensure model files exist in models/ directory!")
    raise

# ============================================================================
# HELPER FUNCTIONS - FEATURE ENGINEERING (MATCH DENGAN TRAINING!)
# ============================================================================

def clean_categorical_value(value):
    """Bersihkan nilai kategorikal untuk konsistensi"""
    s = str(value).strip()
    if s.endswith('.0'):
        s = s[:-2]
    return s

def calculate_shift(hour):
    """Hitung shift (8 shift, interval 3 jam)"""
    shift_index = hour // 3
    return f'shift_{shift_index + 1}'

def get_lookup_value(lookup_dict, key, default_value):
    """Ambil nilai dari dictionary lookup dengan aman"""
    return lookup_dict.get(key, default_value)

def validate_stack_for_block(tier_val, block_num):
    """
    Validasi bahwa tier/stack yang dikirim sesuai dengan block tujuan.
    
    Args:
        tier_val: Stack/Tier yang dikirim (bisa "1", "2", ..., "D1", "7", dll)
        block_num: Block ID tujuan (1-7)
    
    Returns:
        tuple: (is_valid: bool, error_message: str)
    """
    try:
        block_id = int(block_num)

        # Block D1 tetap strict: wajib stack D1
        if block_id == 7:
            tier_normalized = str(tier_val).strip().upper()
            valid_stacks = BLOCK_VALID_STACKS.get(block_id, [])
            if tier_normalized not in valid_stacks:
                return False, (
                    f"Stack '{tier_val}' tidak diizinkan untuk block {BLOCK_LABELS[block_id]}. "
                    f"Block ini hanya menerima stack: {', '.join(valid_stacks)}"
                )
            return True, ""

        # Untuk CY1-CY6, izinkan semua stack (relaksasi agar prediksi tidak macet)
        if block_id < 1 or block_id > 7:
            return False, f"Invalid block ID: {block_id}"
        return True, ""

    except Exception as e:
        return False, f"Validation error: {str(e)}"

def engineer_features(input_data):
    """
    Rekayasa SEMUA 45 fitur dari data input mentah.
    MATCH DENGAN TRAINING DATASET 2 BULAN!
    """
    
    df = pd.DataFrame([input_data])
    overall_avg = lookup_tables['overall_avg']
    
    # ========================================================================
    # 1. BERSIHKAN FITUR KATEGORI
    # ========================================================================
    
    df['slot'] = df['slot'].apply(clean_categorical_value)
    df['tier'] = df['tier'].apply(clean_categorical_value)
    df['block'] = df['block'].apply(clean_categorical_value)
    
    if 'row' in df.columns:
        df['row'] = df['row'].apply(clean_categorical_value)
        df['row_numeric'] = pd.to_numeric(df['row'], errors='coerce').fillna(0).astype(int)
    else:
        df['row_numeric'] = 0
    
    # Buat LOKASI
    df['LOKASI'] = df['slot'] + ' ' + df['row_numeric'].astype(str) + ' ' + df['tier']
    
    # ========================================================================
    # 2. FITUR WAKTU
    # ========================================================================
    
    gate_in_raw = input_data.get('gate_in_time') or input_data.get('gate_in') or datetime.now().isoformat()
    try:
        gate_in_dt = pd.to_datetime(gate_in_raw)
        if pd.isna(gate_in_dt):
            gate_in_dt = pd.Timestamp(datetime.now())
    except Exception:
        gate_in_dt = pd.Timestamp(datetime.now())
    
    current_time = gate_in_dt.to_pydatetime()
    df['gate_in_hour'] = current_time.hour
    df['gate_in_dayofweek'] = current_time.weekday()
    df['gate_in_day'] = current_time.day
    df['gate_in_month'] = current_time.month
    
    # Hitung shift (8 shift, interval 3 jam)
    df['gate_in_shift'] = df['gate_in_hour'].apply(calculate_shift)
    
    df['gate_in_is_weekend'] = (df['gate_in_dayofweek'] >= 5).astype(int)
    df['gate_in_is_peak'] = df['gate_in_hour'].isin([9, 10, 11, 13, 14, 15]).astype(int)
    
    # ========================================================================
    # 3. FITUR LOKASI NUMERIK
    # ========================================================================
    
    df['slot_numeric'] = pd.to_numeric(df['slot'], errors='coerce').fillna(0).astype(int)
    df['tier_numeric'] = pd.to_numeric(df['tier'], errors='coerce').fillna(0).astype(int)
    df['block_numeric'] = df['block'].str.extract(r'(\d+)').astype(float).fillna(0).astype(int)
    
    df['distance_from_gate'] = (
        df['slot_numeric'] * 10 + 
        df['row_numeric'] * 2 + 
        df['tier_numeric'] * 3
    )
    df['vertical_distance'] = df['tier_numeric'] ** 2
    
    # ========================================================================
    # 4. FITUR KEPADATAN
    # ========================================================================
    
    df['hourly_volume'] = df['gate_in_hour'].apply(
        lambda h: get_lookup_value(lookup_tables['hourly_volume'], h, 50)
    )
    
    df['hour_slot_key'] = df['gate_in_hour'].astype(str) + '_' + df['slot']
    df['congestion_count'] = df['hour_slot_key'].apply(
        lambda k: get_lookup_value(lookup_tables['congestion_by_hour_slot'], k, 10)
    )
    
    # ========================================================================
    # 5. FITUR HISTORIS
    # ========================================================================
    
    df['slot_historical_avg'] = df['slot'].apply(
        lambda s: get_lookup_value(lookup_tables['slot_historical_avg'], s, overall_avg)
    )
    
    df['tier_historical_avg'] = df['tier'].apply(
        lambda t: get_lookup_value(lookup_tables['tier_historical_avg'], t, overall_avg)
    )
    
    df['lokasi_historical_avg'] = df['LOKASI'].apply(
        lambda l: get_lookup_value(lookup_tables['lokasi_historical_avg'], l, overall_avg)
    )
    
    df['hour_historical_avg'] = df['gate_in_hour'].apply(
        lambda h: get_lookup_value(lookup_tables['hour_historical_avg'], h, overall_avg)
    )
    
    # ========================================================================
    # 6. FITUR KONTAINER
    # ========================================================================
    
    df['container_size_numeric'] = pd.to_numeric(
        df['CONTAINER_SIZE'].astype(str).str.extract(r'(\d+)')[0], 
        errors='coerce'
    ).fillna(20).astype(int)
    
    df['is_empty'] = (df['CTR_STATUS'] == 'MTY').astype(int)
    df['is_full'] = (df['CTR_STATUS'] == 'FCL').astype(int)
    df['is_reefer'] = df['CONTAINER_TYPE'].str.contains('RF|REEFER|RH', case=False, na=False).astype(int)
    df['is_special'] = df['CONTAINER_TYPE'].str.contains('OT|FR|FLAT|OPEN', case=False, na=False).astype(int)
    
    # ========================================================================
    # 7. FITUR JAM SIBUK
    # ========================================================================
    
    df['is_morning_rush'] = df['gate_in_hour'].isin([8, 9, 10]).astype(int)
    df['is_afternoon_rush'] = df['gate_in_hour'].isin([13, 14, 15]).astype(int)
    df['is_rush_hour'] = (df['is_morning_rush'] | df['is_afternoon_rush']).astype(int)
    
    # ========================================================================
    # 8. FITUR INTERAKSI NUMERIK
    # ========================================================================
    
    df['slot_tier_interaction'] = df['slot_numeric'] * df['tier_numeric']
    df['size_tier_interaction'] = df['container_size_numeric'] * df['tier_numeric']
    df['congestion_tier'] = df['congestion_count'] * df['tier_numeric']
    df['rush_hour_congestion'] = df['is_rush_hour'] * df['congestion_count']
    
    # ========================================================================
    # 9. FITUR STATISTIK
    # ========================================================================
    
    df['slot_duration_std'] = df['slot'].apply(
        lambda s: get_lookup_value(lookup_tables['slot_duration_std'], s, 0)
    )
    df['slot_duration_min'] = df['slot'].apply(
        lambda s: get_lookup_value(lookup_tables['slot_duration_min'], s, 7.35)
    )
    df['slot_duration_max'] = df['slot'].apply(
        lambda s: get_lookup_value(lookup_tables['slot_duration_max'], s, 42.47)
    )
    
    # ========================================================================
    # 10. FITUR LAG
    # ========================================================================
    
    location_key = df['LOKASI'].iloc[0]
    location_hist = lookup_tables['location_history'].get(location_key, None)
    
    if location_hist:
        df['prev_duration_same_location'] = location_hist['last_duration']
        df['rolling_mean_3'] = location_hist['rolling_mean_3']
    else:
        df['prev_duration_same_location'] = df['lokasi_historical_avg']
        df['rolling_mean_3'] = df['lokasi_historical_avg']
    
    # ========================================================================
    # 11. TARGET ENCODING
    # ========================================================================
    
    df['BLOCK_target_enc'] = df['block'].apply(
        lambda b: get_lookup_value(lookup_tables['BLOCK_target_enc'], b, overall_avg)
    )
    df['LOKASI_target_enc'] = df['lokasi_historical_avg']
    
    # ========================================================================
    # 12. PILIH DAN URUTKAN FITUR
    # ========================================================================
    
    categorical_features = [
        'JOB_TYPE', 'CONTAINER_SIZE', 'CTR_STATUS', 'CONTAINER_TYPE',
        'slot', 'tier', 'block', 'gate_in_shift'
    ]
    
    numerical_features = [
        'gate_in_hour', 'gate_in_dayofweek', 'gate_in_day', 'gate_in_month',
        'gate_in_is_weekend', 'gate_in_is_peak',
        'slot_numeric', 'row_numeric', 'tier_numeric', 'block_numeric',
        'distance_from_gate', 'vertical_distance',
        'hourly_volume', 'congestion_count',
        'slot_historical_avg', 'tier_historical_avg', 
        'lokasi_historical_avg', 'hour_historical_avg',
        'container_size_numeric', 'is_empty', 'is_full', 'is_reefer', 'is_special',
        'is_morning_rush', 'is_afternoon_rush', 'is_rush_hour',
        'slot_tier_interaction', 'size_tier_interaction',
        'congestion_tier', 'rush_hour_congestion',
        'slot_duration_std', 'slot_duration_min', 'slot_duration_max',
        'prev_duration_same_location', 'rolling_mean_3',
        'BLOCK_target_enc', 'LOKASI_target_enc'
    ]
    
    all_features = categorical_features + numerical_features
    
    # ========================================================================
    # 13. LABEL ENCODE UNTUK FITUR KATEGORI
    # ========================================================================
    
    for col in categorical_features:
        if col in df.columns and col in label_encoders:
            le = label_encoders[col]
            try:
                unknown_mask = ~df[col].isin(le.classes_)
                unknown_count = unknown_mask.sum()
                if unknown_count > 0:
                    print(f"Warning {col}: {unknown_count} unseen values replaced with {le.classes_[0]}")
                    df.loc[unknown_mask, col] = le.classes_[0]
                df[col] = le.transform(df[col])
            except Exception as e:
                print(f"Warning: Could not encode {col}: {e}")
                df[col] = 0
    
    # ========================================================================
    # 14. KEMBALIKAN VEKTOR FITUR FINAL
    # ========================================================================
    
    # Penting: urutkan fitur agar sesuai urutan pelatihan
    print(f"\nReordering features to match features_list...")
    print(f"   Features in engineer_features: {len(all_features)}")
    print(f"   Features in features_list: {len(features_list)}")
    
    # Gunakan urutan features_list dari training
    X = df[features_list].copy()
    X = X.fillna(0)
    
    print(f"   Features reordered successfully")
    
    return X

def predict_duration(truck_data):
    """
    Prediksi durasi pemrosesan truk
    
    Input: data truk dengan field yang diperlukan
    Output: durasi prediksi dalam menit
    """
    try:
        print("\n" + "="*60)
        print("DEBUG - PREDICT_DURATION")
        print("="*60)
        print(f"Input truck_data: {truck_data}")
        
        # Siapkan data untuk prediksi
        input_data = {
            'JOB_TYPE': truck_data.get('job_type', 'DELIVERY'),
            'CONTAINER_SIZE': str(truck_data.get('container_size', '40')),
            'CTR_STATUS': truck_data.get('ctr_status', 'FULL'),
            'CONTAINER_TYPE': truck_data.get('container_type', 'DRY'),
            'slot': str(truck_data.get('slot', '1')),
            'tier': str(truck_data.get('tier', '1')),
            'block': str(truck_data.get('block', '1G')),
            'row': str(truck_data.get('row', '1')),
            'gate_in_time': truck_data.get('gate_in_time', datetime.now().isoformat())
        }
        
        print(f"\nPrepared input_data:")
        for k, v in input_data.items():
            print(f"  {k}: {v} (type: {type(v).__name__})")
        
        # Engineer features
        print("\nEngineering features...")
        X = engineer_features(input_data)
        
        print(f"Features engineered successfully")
        print(f"   Shape: {X.shape}")
        print(f"   Columns: {X.shape[1]}")
        
        # Periksa nilai NaN/inf
        nan_count = X.isna().sum().sum()
        inf_count = np.isinf(X.values).sum()
        print(f"   NaN values: {nan_count}")
        print(f"   Inf values: {inf_count}")
        
        # Cetak 10 nilai fitur pertama
        print(f"\nFirst 10 feature values:")
        for i in range(min(10, X.shape[1])):
            col_name = X.columns[i]
            col_value = X.iloc[0, i]
            print(f"  {i+1}. {col_name:30s} = {col_value}")
        
        # Lakukan prediksi
        print("\nCalling model.predict()...")
        prediction = model.predict(X)[0]
        
        print(f"PREDICTION SUCCESS: {prediction:.2f} minutes")
        print("="*60 + "\n")
        
        return round(prediction, 2)
        
    except Exception as e:
        print(f"\nERROR IN PREDICTION")
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {str(e)}")
        print(f"\nFull traceback:")
        print(traceback.format_exc())
        print(f"\nReturning fallback mean: {lookup_tables['metadata']['target_mean']:.2f}")
        print("="*60 + "\n")
        
        return lookup_tables['metadata']['target_mean']

# ============================================================================
# FUNGSI PERHITUNGAN STATISTIK
# ============================================================================

def calculate_block_stats(block_id):
    """Hitung statistik untuk satu blok."""
    queue = QUEUES[block_id]
    
    if len(queue) == 0:
        return {
            'count': 0,
            'avg_duration': 0.0,
            'total_duration': 0.0,
            'min_duration': 0.0,
            'max_duration': 0.0
        }
    
    # Ambil semua durasi prediksi
    durations = [truck['predicted_duration'] for truck in queue]
    
    return {
        'count': len(queue),
        'avg_duration': round(sum(durations) / len(durations), 2),
        'total_duration': round(sum(durations), 2),
        'min_duration': round(min(durations), 2),
        'max_duration': round(max(durations), 2)
    }

def calculate_global_stats():
    """Hitung statistik gabungan untuk semua blok."""
    all_durations = []
    blocks_with_trucks = 0
    
    for block_id in range(1, 8):  # 7 blok
        queue = QUEUES[block_id]
        if len(queue) > 0:
            blocks_with_trucks += 1
            durations = [truck['predicted_duration'] for truck in queue]
            all_durations.extend(durations)
    
    if len(all_durations) == 0:
        return {
            'total_trucks': 0,
            'avg_duration': 0.0,
            'total_duration': 0.0,
            'blocks_with_trucks': 0
        }
    
    return {
        'total_trucks': len(all_durations),
        'avg_duration': round(sum(all_durations) / len(all_durations), 2),
        'total_duration': round(sum(all_durations), 2),
        'blocks_with_trucks': blocks_with_trucks
    }

# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.route('/')
def home():
    """Endpoint kesehatan untuk memastikan layanan aktif."""
    return jsonify({
        'status': 'running',
        'service': 'ARTG Multi-Block Queue Management',
        'model': 'LightGBM',
        'features': len(features_list),
        'shift_type': lookup_tables['metadata']['shift_type'],
        'blocks': len(BLOCK_LABELS),
        'version': '2.0'
    })

@app.route('/blocks', methods=['GET'])
def get_blocks():
    """Mengambil data semua blok beserta antrian dan panjangnya."""
    try:
        blocks_data = {}
        
        for block_id in range(1, 8):  # 7 blocks
            blocks_data[str(block_id)] = {
                'name': BLOCK_LABELS[block_id],
                'queue': QUEUES[block_id],
                'queue_length': len(QUEUES[block_id])
            }
        
        return jsonify(blocks_data)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/blocks/<int:block_id>/stats', methods=['GET'])
def get_block_stats(block_id):
    """Mengambil statistik untuk blok tertentu."""
    try:
        if block_id < 1 or block_id > 7:
            return jsonify({'error': 'Invalid block ID (must be 1-7)'}), 400
        
        stats = calculate_block_stats(block_id)
        return jsonify(stats)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/stats', methods=['GET'])
def get_global_stats():
    """Mengambil statistik gabungan seluruh blok."""
    try:
        stats = calculate_global_stats()
        return jsonify(stats)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/blocks/<int:block_id>/add_truck', methods=['POST'])
def add_truck(block_id):
    """Tambah truk ke antrian blok dengan prediksi durasi menggunakan model."""
    try:
        if block_id < 1 or block_id > 7:
            return jsonify({'error': 'Invalid block ID (must be 1-7)'}), 400
        
        data = request.get_json()
        
        # Validasi field wajib
        required_fields = ['truck_id', 'lokasi']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Parsing lokasi (format: "slot row tier")
        lokasi_parts = data['lokasi'].strip().split()
        if len(lokasi_parts) != 3:
            return jsonify({'error': 'Invalid lokasi format (expected: "slot row tier")'}), 400
        
        slot, row, tier = lokasi_parts
        
        # Siapkan data truk untuk prediksi
        truck_data = {
            'truck_id': data['truck_id'],
            'job_type': data.get('job_type', 'DELIVERY'),
            'container_size': data.get('container_size', '40'),
            'container_type': data.get('container_type', 'DRY'),
            'ctr_status': data.get('ctr_status', 'FULL'),
            'slot': slot,
            'row': row,
            'tier': tier,
            'block': data.get('block', '1G')
        }
        
        # Prediksi durasi menggunakan model ML
        predicted_duration = predict_duration(truck_data)
        
        # Hitung gate_in_time dan expected_ready_time
        from datetime import timedelta
        gate_in_time = datetime.now()
        expected_ready_time = gate_in_time + timedelta(minutes=predicted_duration)
        
        # Bentuk objek truk yang akan disimpan
        truck = {
            'truck_id': truck_data['truck_id'],
            'job_type': truck_data['job_type'],
            'container_size': truck_data['container_size'],
            'container_type': truck_data['container_type'],
            'ctr_status': truck_data['ctr_status'],
            'lokasi': data['lokasi'],
            'slot': slot,
            'row': row,
            'tier': tier,
            'block': truck_data['block'],
            'predicted_duration': predicted_duration,
            'gate_in_time': gate_in_time.strftime('%Y-%m-%d %H:%M:%S'),
            'expected_ready_time': expected_ready_time.strftime('%Y-%m-%d %H:%M:%S'),
            'added_at': gate_in_time.isoformat()
        }
        
        # Tambahkan ke antrian
        QUEUES[block_id].append(truck)
        
        return jsonify({
            'truck': truck,
            'message': f'Truck {truck["truck_id"]} added successfully to {BLOCK_LABELS[block_id]}'
        })
        
    except Exception as e:
        print(f"ERROR adding truck: {e}")
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@app.route('/blocks/<int:block_id>/truck/<int:truck_index>', methods=['DELETE'])
def remove_truck(block_id, truck_index):
    """Hapus truk dari antrian blok berdasarkan indeks."""
    try:
        if block_id < 1 or block_id > 7:
            return jsonify({'error': 'Invalid block ID (must be 1-7)'}), 400
        
        queue = QUEUES[block_id]
        
        if truck_index < 0 or truck_index >= len(queue):
            return jsonify({'error': 'Invalid truck index'}), 400
        
        removed_truck = queue.pop(truck_index)
        
        return jsonify({
            'message': f'Truck {removed_truck["truck_id"]} removed successfully',
            'removed_truck': removed_truck
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/blocks/<int:block_id>/clear', methods=['POST'])
def clear_block(block_id):
    """Kosongkan seluruh antrian pada satu blok."""
    try:
        if block_id < 1 or block_id > 7:
            return jsonify({'error': 'Invalid block ID (must be 1-7)'}), 400
        
        count = len(QUEUES[block_id])
        QUEUES[block_id] = []
        
        return jsonify({
            'message': f'{BLOCK_LABELS[block_id]} cleared successfully',
            'trucks_removed': count
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/demo/populate', methods=['POST'])
def populate_demo_data():
    """Mengisi data demo untuk pengujian cepat."""
    try:
        # Kosongkan data yang ada
        for block_id in range(1, 8):
            QUEUES[block_id] = []
        
        # Konfigurasi truk demo
        demo_trucks = [
            {
                'block_id': 1,
                'truck_id': 'L9088UE',
                'job_type': 'DELIVERY',
                'size': '40',
                'type': 'DRY',
                'status': 'FULL',
                'lokasi': '42 06 1',
                'block': '1G'
            },
            {
                'block_id': 1,
                'truck_id': 'H1917DW',
                'job_type': 'DELIVERY',
                'size': '40',
                'type': 'DRY',
                'status': 'FULL',
                'lokasi': '76 02 1',
                'block': '1E'
            },
            {
                'block_id': 2,
                'truck_id': 'G8190OA',
                'job_type': 'DELIVERY',
                'size': '20',
                'type': 'DRY',
                'status': 'FULL',
                'lokasi': '31 04 2',
                'block': '2A'
            },
            {
                'block_id': 2,
                'truck_id': 'H1647EA',
                'job_type': 'RECEIVING',
                'size': '20',
                'type': 'DRY',
                'status': 'FULL',
                'lokasi': '13 05 2',
                'block': '2C'
            },
            {
                'block_id': 3,
                'truck_id': 'B9319BEI',
                'job_type': 'DELIVERY',
                'size': '40',
                'type': 'OVD',
                'status': 'MTY',
                'lokasi': '78 03 1',
                'block': '3Z'
            },
            {
                'block_id': 4,
                'truck_id': 'E9015AD',
                'job_type': 'DELIVERY',
                'size': '20',
                'type': 'DRY',
                'status': 'MTY',
                'lokasi': '15 10 1',
                'block': '4B'
            },
            {
                'block_id': 5,
                'truck_id': 'H9331OW',
                'job_type': 'RECEIVING',
                'size': '20',
                'type': 'DRY',
                'status': 'FULL',
                'lokasi': '17 01 1',
                'block': '5G'
            }
            
        ]
        
        added_count = 0
        for truck_config in demo_trucks:
            # Parsing lokasi menjadi slot, row, tier
            lokasi_parts = truck_config['lokasi'].split()
            slot = lokasi_parts[0]
            row = lokasi_parts[1]
            tier = lokasi_parts[2]
            
            truck_data = {
                'truck_id': truck_config['truck_id'],
                'job_type': truck_config['job_type'],
                'container_size': truck_config['size'],
                'container_type': truck_config['type'],
                'ctr_status': truck_config['status'],
                'slot': slot,
                'row': row,
                'tier': tier,
                'block': truck_config['block']
            }
            
            print(f"\nAdding demo truck: {truck_config['truck_id']}")
            predicted_duration = predict_duration(truck_data)
            print(f"   Predicted: {predicted_duration} min")
            
            # Hitung gate_in_time dan expected_ready_time
            from datetime import timedelta
            gate_in_time = datetime.now()
            expected_ready_time = gate_in_time + timedelta(minutes=predicted_duration)
            
            truck = {
                'truck_id': truck_data['truck_id'],
                'job_type': truck_data['job_type'],
                'container_size': truck_data['container_size'],
                'container_type': truck_data['container_type'],
                'ctr_status': truck_data['ctr_status'],
                'lokasi': truck_config['lokasi'],
                'slot': slot,
                'row': row,
                'tier': tier,
                'block': truck_data['block'],
                'predicted_duration': predicted_duration,
                'gate_in_time': gate_in_time.strftime('%Y-%m-%d %H:%M:%S'),
                'expected_ready_time': expected_ready_time.strftime('%Y-%m-%d %H:%M:%S'),
                'added_at': gate_in_time.isoformat()
            }
            
            QUEUES[truck_config['block_id']].append(truck)
            added_count += 1
        
        print(f"\nDemo data populated: {added_count} trucks added")
        
        return jsonify({
            'message': f'Demo data populated successfully',
            'trucks_added': added_count
        })
        
    except Exception as e:
        print(f"\nERROR populating demo data: {e}")
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

# ============================================================================
# WEBSOCKET EVENTS (Real-time Prediction)
# ============================================================================

@socketio.on('connect')
def handle_connect():
    """Tangani koneksi klien."""
    logger.info(f'Client connected: {request.sid}')
    # Initialize cache cleanup on first connection
    initialize_cache_cleanup()
    emit('connection_response', {
        'status': 'connected',
        'message': 'Connected to Flask SocketIO backend',
        'model': 'Stacking Ensemble (LightGBM+XGBoost+CatBoost)',
        'blocks': len(BLOCK_LABELS)
    })

@socketio.on('disconnect')
def handle_disconnect():
    """Tangani pemutusan koneksi klien."""
    logger.info(f'Client disconnected: {request.sid}')

@socketio.on('GATE_IN_DATA')
def handle_gate_in(data):
    """Menerima data truk real-time dari WebSocket (via React)."""
    
    try:
        logger.info(f"Received GATE_IN_DATA: {data}")
        
        # Ambil truck_id dan gate_in_time untuk deduplikasi
        truck_id = data.get('truck_id') or data.get('TRUCK_ID', 'UNKNOWN')
        gate_in_time = data.get('GATE_IN_TIME') or data.get('gate_in_time') or datetime.now().isoformat()
        
        # Bentuk kunci deduplikasi
        dedup_key = f"{truck_id}_{gate_in_time}"
        
        logger.info(f"Checking cache | Key: {dedup_key} | Cache size: {len(processed_trucks_cache)}")
        
        # Cek apakah sudah pernah diproses
        with cache_lock:
            if dedup_key in processed_trucks_cache:
                logger.warning(f"Duplicate detected - skipping prediction for {truck_id}")
                return
            # Mark as processed
            processed_trucks_cache[dedup_key] = time.time()
            logger.info(f"New truck registered: {truck_id} | Cache size: {len(processed_trucks_cache)}")

        # Ambil block dari payload
        raw_block = data.get('to_block') or data.get('TO_BLOCK')
        raw_block_str = None
        block_num = None
        if raw_block:
            raw_block_str = str(raw_block).strip()
            # Jika format D1 maka blok = 7 (D1)
            if raw_block_str.upper().startswith('D'):
                block_num = '7'
            # Jika format "5A" ambil digit pertama
            elif raw_block_str and raw_block_str[0].isdigit():
                block_num = raw_block_str[0]

        block_num = block_num or str(data.get('block') or data.get('BLOCK') or '1')
        raw_block_str = (raw_block_str or str(data.get('block') or data.get('BLOCK') or block_num)).strip()
        block_id = int(block_num)

        # Pakai field asli dari payload websocket (trim spasi)
        slot_val = str(data.get('X') or data.get('slot') or data.get('SLOT') or 1).strip()
        row_val = str(data.get('Y') or data.get('row') or data.get('ROW') or 1).strip()
        tier_val = str(data.get('Z') or data.get('tier') or data.get('TIER') or 1).strip()

        # ===================================================================
        # VALIDASI STACK/TIER UNTUK BLOCK
        # ===================================================================
        is_valid_stack, validation_error = validate_stack_for_block(tier_val, block_id)
        
        if not is_valid_stack:
            logger.error(f"VALIDATION FAILED for truck {truck_id}: {validation_error}")
            logger.error(f"   Requested block: {BLOCK_LABELS.get(block_id, 'UNKNOWN')}")
            logger.error(f"   Stack received: {tier_val}")
            
            # Emit rejection event ke klien
            emit('PREDICTION_REJECTED', {
                'truck_id': truck_id,
                'block': block_id,
                'stack': tier_val,
                'reason': validation_error,
                'timestamp': datetime.now().isoformat(),
                'status': 'rejected',
                'message': f"Truck {truck_id} DITOLAK: {validation_error}"
            }, broadcast=True)
            
            return  # REJECT truck ini, jangan lanjutkan prediksi

        logger.info(f"Stack validation passed for truck {truck_id}")
        logger.info(f"   Block: {BLOCK_LABELS[block_id]} | Stack: {tier_val}")

        # Informasi kontainer (fallback ke default jika kosong)
        container_size = str(data.get('CTR_SIZE') or data.get('container_size') or data.get('CONTAINER_SIZE') or 40).strip()
        container_type = (data.get('CTR_TYPE') or data.get('container_type') or data.get('CONTAINER_TYPE') or 'DRY').strip()
        ctr_status = (data.get('CTR_STATUS') or data.get('ctr_status') or 'FCL').strip()

        # Aktivitas / tipe pekerjaan
        activity = (data.get('activity') or data.get('ACTIVITY') or '').strip().upper()
        job_type = data.get('job_type') or ('EXPORT' if activity == 'DELIVERY' else 'IMPORT')

        # Gunakan label blok yang sesuai dataset untuk fitur
        # Untuk D1 selalu pakai "D1"; untuk CY gunakan kode asli (mis. 1G/2C) agar variasi fitur tidak hilang
        block_for_features = 'D1' if block_id == 7 else (raw_block_str or str(block_id))

        # Siapkan truck_data untuk engineer_features
        truck_data = {
            'JOB_TYPE': job_type,
            'CONTAINER_SIZE': container_size,
            'CTR_STATUS': ctr_status,
            'CONTAINER_TYPE': container_type,
            'slot': slot_val,
            'row': row_val,
            'tier': tier_val,
            'block': block_for_features,
            'gate_in_time': gate_in_time
        }
        
        logger.info(f"Prepared truck_data for {truck_id}:")
        logger.info(f"   Location: slot={slot_val}, row={row_val}, tier={tier_val}")
        logger.info(f"   Block: {block_num}, Job: {truck_data['JOB_TYPE']}, Size: {container_size}, Status: {ctr_status}")
        
        # Rekayasa fitur menggunakan fungsi yang sudah diuji
        X_input = engineer_features(truck_data)
        
        # Prediksi
        prediction = model.predict(X_input)[0]
        logger.info(f"Prediction: {prediction:.2f} min for truck {truck_id}")
        
        # Kirim hasil prediksi
        emit('PREDICTION_RESULT', {
            'truck_id': truck_id,
            'predicted_duration_minutes': float(prediction),
            'block': block_id,
            'confidence': 0.85,
            'timestamp': datetime.now().isoformat(),
            'status': 'success'
        }, broadcast=True)
        
    except Exception as e:
        logger.error(f"Error in GATE_IN_DATA: {str(e)}", exc_info=True)

# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    print("\n" + "="*80)
    print("ARTG MULTI-BLOCK QUEUE MANAGEMENT API (with Real-time WebSocket)")
    print("="*80)
    print(f"Model: Stacking Ensemble (LightGBM + XGBoost + CatBoost + Ridge)")
    print(f"Features: {len(features_list)}")
    print(f"Performance: MAE 6.25 min | R2 0.26 | 82% within 10min")
    print(f"Shift type: {lookup_tables['metadata']['shift_type']}")
    print(f"Blocks: {len(BLOCK_LABELS)}")
    print(f"WebSocket: Enabled")
    print(f"Ready to serve real-time predictions!")
    print("="*80 + "\n")
    
    # Jalankan dengan dukungan SocketIO
    socketio.run(app, debug=True, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)