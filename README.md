# 🚢 ARTG Truck Queue Prediction System
**Real-Time Queue Management & Duration Prediction for Port Container Yard**

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![React](https://img.shields.io/badge/React-18.2-61dafb.svg)](https://reactjs.org/)
[![License](https://img.shields.io/badge/License-Proprietary-red.svg)](LICENSE)

---

## 📋 Deskripsi Project

Sistem prediksi dan manajemen antrian truk real-time untuk operasional **ARTG (Automated Rail Mounted Gantry)** di pelabuhan. Project ini mengintegrasikan **Machine Learning** dengan **WebSocket real-time streaming** untuk memprediksi durasi pemrosesan truk kontainer dari gate-in hingga stack.

### 🎯 Tujuan Bisnis
- ✅ Memprediksi waktu tunggu truk secara akurat (target: MAE < 7 menit)
- ✅ Optimasi alokasi sumber daya berdasarkan prediksi antrian
- ✅ Monitoring real-time untuk 7 blok container yard (CY1-CY6, D1)
- ✅ Meningkatkan efisiensi operasional pelabuhan

### ⚡ Key Features
- **Real-time WebSocket Integration** - Data streaming langsung dari server eksternal
- **ML Ensemble Model** - Stacking (LightGBM + XGBoost + CatBoost + Ridge)
- **45 Engineered Features** - Temporal, spatial, congestion, historical patterns
- **Dual Mode Operation** - Batch mode (manual input) & Real-time mode (live queue)
- **Multi-block Management** - 7 blok yard dengan antrian independen
- **Data Validation** - Strict validation untuk data integrity

---

## 🏗️ Arsitektur Sistem

```
┌─────────────────────────────────────────────────────────────────┐
│                    SISTEM PREDIKSI ARTG                        │
└─────────────────────────────────────────────────────────────────┘

┌──────────────────┐      WebSocket       ┌──────────────────────┐
│  External Server │ ──────────────────>  │   React Frontend     │
│  (10.130.0.176)  │   GATE_IN Events     │   (Port 3000)        │
└──────────────────┘                       └──────────────────────┘
                                                    │
                                            WebSocket (Socket.io)
                                                    │
┌────────────────────────────────────────────────────────────────┐
│                     FLASK BACKEND (Port 5000)                  │
│                                                                │
│  ┌──────────────┐    ┌─────────────────┐    ┌──────────────┐ │
│  │  WebSocket   │───>│ Feature Engineer │───>│ ML Ensemble  │ │
│  │   Handler    │    │   (45 features)  │    │    Model     │ │
│  └──────────────┘    └─────────────────┘    └──────────────┘ │
│         │                                            │         │
│         │                                            │         │
│  ┌──────▼─────────────────────────────────────┐     │         │
│  │    Deduplication Cache (TTL 60s)          │     │         │
│  │  + Validation (slot/row/tier mandatory)    │     │         │
│  └────────────────────────────────────────────┘     │         │
│                                                      │         │
│  ┌───────────────────────────────────────────────────▼──────┐ │
│  │      Queue Management (7 Blocks: CY1-CY6, D1)            │ │
│  │      + Statistics Calculation                            │ │
│  └──────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────┘
         │                                         │
         │ Prediction Results                      │ Queue Stats
         ▼                                         ▼
┌─────────────────────────────────────────────────────────────────┐
│              React Dashboard (Real-time Updates)               │
│  • Block Selection   • Queue Visualization   • Statistics      │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📊 Machine Learning Pipeline

### **1️⃣ Data Cleaning** (`cleaning_raw_data2bulan_NEW.ipynb`)

**Input:** `gatein_out_2bulan.csv` (raw data 2 bulan)  
**Output:** `dataset_rapi_2bulan.csv` (105,995 records)

**Proses:**
```
Raw Data (150k+ records)
    │
    ├─> Remove Block 7 (tidak diprediksi per requirement)
    ├─> Validate SLOT (0-200), ROW (0-50), TIER (0-9)
    ├─> Remove duplicates & missing values
    ├─> Convert datetime columns
    └─> Export cleaned data
```

**Key Validations:**
- ❌ Reject: Block 7 (keputusan bisnis - use D1 instead)
- ❌ Reject: Invalid slot/row/tier ranges
- ❌ Reject: Missing location data (no fallback untuk data integrity)
- ✅ Keep: Slot 102-103 di Block 3Z (valid edge case)

---

### **2️⃣ EDA & Feature Engineering** (`eda_feature_engineering2bulan.ipynb`)

**Input:** `dataset_rapi_2bulan.csv`  
**Output:** `dataset_final2bulan_45FEATURES_PROPER.csv` (96,000 records)

**Transformasi Data:**
```
Cleaned Data (105k records)
    │
    ├─> Outlier Removal: Q5-Q99 (7.35 - 70.83 minutes)
    │
    ├─> 45 FEATURE ENGINEERING PIPELINE:
    │   │
    │   ├─> [1] Location Features (8 features)
    │   │   • slot, row, tier, block (categorical)
    │   │   • slot_numeric, row_numeric, tier_numeric, block_numeric
    │   │   • distance_from_gate = slot*10 + row*2 + tier*3
    │   │   • vertical_distance = tier²
    │   │
    │   ├─> [2] Temporal Features (8 features)
    │   │   • gate_in_hour, dayofweek, day, month
    │   │   • gate_in_shift (8 shifts: 3-hour intervals)
    │   │   • is_weekend, is_peak, is_rush_hour
    │   │
    │   ├─> [3] Congestion Features (2 features)
    │   │   • hourly_volume (lookup by hour)
    │   │   • congestion_count (lookup by hour+slot)
    │   │
    │   ├─> [4] Historical Averages (4 features)
    │   │   • slot_historical_avg
    │   │   • tier_historical_avg
    │   │   • lokasi_historical_avg
    │   │   • hour_historical_avg
    │   │
    │   ├─> [5] Container Features (9 features)
    │   │   • container_size_numeric, ctr_status, container_type
    │   │   • is_empty, is_full, is_reefer, is_special
    │   │   • is_morning_rush, is_afternoon_rush
    │   │
    │   ├─> [6] Interaction Features (4 features)
    │   │   • slot_tier_interaction = slot × tier
    │   │   • size_tier_interaction = size × tier
    │   │   • congestion_tier = congestion × tier
    │   │   • rush_hour_congestion = rush × congestion
    │   │
    │   ├─> [7] Statistical Features (3 features)
    │   │   • slot_duration_std, min, max (from history)
    │   │
    │   ├─> [8] Lag Features (2 features)
    │   │   • prev_duration_same_location
    │   │   • rolling_mean_3 (last 3 trucks at same location)
    │   │
    │   └─> [9] Target Encoding (2 features)
    │       • BLOCK_target_enc
    │       • LOKASI_target_enc
    │
    └─> Export final dataset (96k records × 45 features)
```

**Target Variable:** `GATE_IN_STACK` (processing time in minutes)
- Mean: **22.47 minutes**
- Median: **19.32 minutes**
- Range: **7.35 - 70.83 minutes** (Q5-Q99)

---

### **3️⃣ Model Training & Tuning** (`modeling_45features_PROPER_FIXED.ipynb`)

**Input:** `dataset_final2bulan_45FEATURES_PROPER.csv`  
**Output:** `best_model_2_bulan.pkl` + encoders + lookup tables

**Training Pipeline:**

```
1. Data Preparation
   ├─> Clean categorical values (remove trailing '.0')
   ├─> Split: 80% train (76,800) / 20% test (19,200)
   ├─> Label Encode: 8 categorical features
   ├─> Fill missing: 0 (untuk konsistensi)
   └─> Feature scaling: distance features (0-1 range)

2. Hyperparameter Tuning (Optuna)
   ├─> LightGBM: 50 trials → Best MAE: 6.31 min
   ├─> XGBoost:  50 trials → Best MAE: 6.45 min
   └─> CatBoost: 50 trials → Best MAE: 6.38 min

3. Model Comparison (Test Set)
   ┌───────────────────────┬──────────┬──────────┬────────┐
   │ Model                 │ MAE      │ RMSE     │ R²     │
   ├───────────────────────┼──────────┼──────────┼────────┤
   │ LightGBM (tuned)      │ 6.31 min │ 8.54 min │ 0.721  │
   │ XGBoost (tuned)       │ 6.45 min │ 8.67 min │ 0.712  │
   │ CatBoost (tuned)      │ 6.38 min │ 8.59 min │ 0.718  │
   │ Random Forest         │ 6.89 min │ 9.21 min │ 0.681  │
   │ Gradient Boosting     │ 6.72 min │ 8.98 min │ 0.695  │
   │ ⭐ STACKING ENSEMBLE  │ 6.25 min │ 8.47 min │ 0.726  │ ← BEST
   │ Voting Ensemble       │ 6.34 min │ 8.56 min │ 0.720  │
   └───────────────────────┴──────────┴──────────┴────────┘

4. Final Model: STACKING ENSEMBLE
   • Base learners: LightGBM + XGBoost + CatBoost
   • Meta learner: Ridge Regression
   • Performance:
     - MAE: 6.25 minutes (rata-rata selisih absolut)
     - 82% predictions within 10 minutes error
     - 58% predictions within 5 minutes error
```

**Perbandingan dengan Baseline:**
- **Baseline (Mean Prediction):** MAE = 12.81 minutes
- **Stacking Ensemble:** MAE = 6.25 minutes
- **Improvement:** **51.2% error reduction** 🎯

---

### **4️⃣ Lookup Tables Generation** (`generate_lookups.py`)

**Purpose:** Create pre-computed lookup tables untuk real-time inference

**Output:** `lookup_tables_2bulan.pkl`

```python
lookup_tables = {
    'hourly_volume': {0: 45, 1: 32, ..., 23: 67},
    'congestion_by_hour_slot': {'14_30': 12, '15_45': 8, ...},
    'slot_historical_avg': {'1': 18.5, '2': 19.3, ...},
    'tier_historical_avg': {'1': 17.2, '2': 20.8, ...},
    'lokasi_historical_avg': {'30 1 1': 22.4, ...},
    'hour_historical_avg': {0: 18.3, 1: 17.9, ...},
    'slot_duration_std': {'1': 5.2, '2': 6.1, ...},
    'slot_duration_min': {'1': 7.35, '2': 7.50, ...},
    'slot_duration_max': {'1': 42.5, '2': 45.3, ...},
    'location_history': {
        '30 1 1': {'last_duration': 22.4, 'rolling_mean_3': 21.8},
        ...
    },
    'BLOCK_target_enc': {'1G': 19.2, '2A': 18.5, ...},
    'overall_avg': 22.47,
    'metadata': {
        'shift_type': '8_shifts_3h',
        'target_mean': 22.47,
        'dataset_size': 96000
    }
}
```

**Kegunaan:**
- ⚡ **Fast inference** - no need to recompute aggregations
- 🔒 **Consistency** - same features training vs production
- 📊 **Historical context** - past patterns influence predictions

---

## 🚀 Installation & Setup

### **Prerequisites**
```bash
Python 3.8+
Node.js 16+
4GB RAM minimum
```

### **1. Clone Repository**
```bash
git clone <repository-url>
cd Project1-Magang
```

### **2. Backend Setup**

```bash
# Install Python dependencies
pip install -r requirements.txt

# Verify model files exist (should be included in repo)
ls models/
# Expected files:
#   best_model_2_bulan.pkl
#   label_encoders_2_bulan.pkl
#   features_list_2_bulan.pkl
#   lookup_tables_2bulan.pkl
#   model_metadata_2_bulan.json

# (Optional) Regenerate lookup tables jika data berubah
python generate_lookups.py

# Run backend
python App.py
```

Backend runs on: `http://localhost:5000`

### Frontend Setup

```bash
cd artg-dashboard

# Install dependencies
npm install

# Start development server
npm start
```

Frontend runs on: `http://localhost:3000`

## 📥 Model Files

**Note:** Pre-trained model files are too large for GitHub. Download from:
- [GitHub Releases](https://github.com/Daffa-afaf/ARTG-Queue-Prediction/releases) (recommended)
- or Google Drive link (ask maintainer)

Extract to `models/` folder:
```
models/
├── best_model_2_bulan.pkl
├── all_models_2_bulan.pkl
├── features_list_2_bulan.pkl
├── feature_scaler_2_bulan.pkl
├── label_encoders_2_bulan.pkl
├── lookup_tables_2bulan.pkl
└── model_metadata_2_bulan.json
```

## 🚀 Usage

### 1. Start Backend
```bash
python App.py
# Check: http://10.5.11.242:5000 or http://localhost:5000
```

### 2. Start Frontend
```bash
cd artg-dashboard
npm start
# Opens: http://localhost:3000
```

### 3. Use Dashboard

**Batch Mode:**
- Click "Batch Mode (Manual Input)"
- Select block
- Fill truck details
- Click "Add Truck" → automatic prediction

**Real-time Mode:**
- Click "Real-time Mode (Live Queue)"
- Connect to WebSocket server (auto-connect to 10.130.0.176)
- Trucks appear automatically as they gate-in
- Predictions update in real-time

## 📊 Model Performance

- **MAE:** 6.25 minutes
- **R² Score:** 0.26
- **Accuracy:** 82% within ±10 minutes
- **Features:** 45 engineered features
- **Training Data:** 2 months of historical data

### Feature Engineering

1. **Time Features:** gate_in_hour, day_of_week, shift, peak_hour, weekend
2. **Location Features:** slot, row, tier, distance_from_gate, vertical_distance
3. **Container Features:** size, type, status, is_empty, is_reefer, is_special
4. **Historical Lookup:** avg_by_slot, avg_by_tier, avg_by_location, avg_by_hour
5. **Congestion Features:** hourly_volume, congestion_count, rush_hour
6. **Interactions:** slot_tier, size_tier, congestion_tier, rush_hour_congestion
7. **Statistics:** std, min, max per slot
8. **Lag Features:** previous_duration, rolling_mean

## 📝 Project Structure

```
ARTG-Queue-Prediction/
├── App.py                      # Flask backend
├── requirements.txt            # Python dependencies
├── generate_lookups.py         # Generate lookup tables
├── artg-dashboard/             # React frontend
│   ├── package.json
│   ├── src/
│   │   ├── App.js              # Main app component
│   │   ├── components/
│   │   │   └── RealTimeQueue.js # Real-time mode component
│   │   └── services/
│   │       └── websocketService.js
│   └── public/
├── models/                     # Pre-trained ML models (download separately)
├── Data/                       # Training & testing datasets
├── notebook/                   # Jupyter notebooks for analysis
└── README.md
```

## 🔧 Configuration

### Backend (App.py)
```python
API_URL = "http://10.5.11.242:5000"  # Change if needed
SOCKETIO_PORT = 5000
```

### Frontend (websocketService.js)
```javascript
const externalUrl = 'http://10.130.0.176'      // WebSocket server
const flaskUrl = 'http://10.5.11.242:5000'     // Flask backend
```

Update these URLs if running on different servers.

## 🐛 Troubleshooting

**1. Connection Error to Flask Backend**
- Ensure `App.py` is running
- Check firewall/port 5000
- Update URL in `websocketService.js` to match your backend

**2. Model Not Found**
- Download models from Releases
- Extract to `models/` folder
- Ensure all `.pkl` files are present

**3. Real-time Not Connecting**
- Check external WebSocket server URL
- Ensure 10.130.0.176 is accessible from your network
- Check console logs for connection errors

**4. Predictions Stuck on "Processing"**
- Check backend logs for errors
- Verify truck data has all required fields (slot, row, tier)
- Ensure block-stack validation passes

## 📚 API Endpoints

### REST
- `GET /blocks` - Get all blocks queue
- `GET /blocks/{id}/stats` - Block statistics
- `POST /blocks/{id}/add_truck` - Add truck manually
- `DELETE /blocks/{id}/clear` - Clear block queue
- `POST /demo/populate` - Load demo data

### WebSocket
- `GATE_IN` - Incoming truck data
- `GATE_IN_DATA` - Send truck to prediction
- `PREDICTION_RESULT` - Receive prediction
- `PREDICTION_ERROR` - Error notification
- `PREDICTION_REJECTED` - Validation rejected

## 👥 Contributors

- Daffa (Development & ML)

## 📄 License

Internal project for PELINDO III - ARTG Terminal

## 📞 Support

For issues or questions, contact the development team.

---

**Last Updated:** January 2026
