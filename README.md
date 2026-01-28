# ARTG Queue Prediction System

Real-time truck queue duration prediction system for ARTG Pelabuhan using machine learning ensemble model.

## 📋 Overview

Multi-block truck queue management system with:
- **Real-time WebSocket** integration for live truck data
- **ML Ensemble Model** (LightGBM + XGBoost + CatBoost + Ridge) for duration prediction
- **Flask Backend** with 45 engineered features
- **React Dashboard** with batch mode (manual input) and real-time mode (live queue)

## 🎯 Features

- **Batch Mode**: Manual truck input with instant prediction
- **Real-time Mode**: Live WebSocket streaming from external server
- **Multi-block Management**: 7 container yard blocks (CY1-CY6, D1)
- **Duration Prediction**: MAE 6.25 minutes, 82% accuracy within 10min
- **Statistics Dashboard**: Queue stats, arrival trends, duration analysis

## 🛠️ Tech Stack

**Backend:**
- Flask + Flask-SocketIO
- Python 3.8+
- scikit-learn, LightGBM, XGBoost, CatBoost
- Pandas, NumPy

**Frontend:**
- React 18+
- Tailwind CSS
- Socket.io Client
- Lucide React Icons

## 📦 Installation

### Prerequisites
- Python 3.8+
- Node.js 16+
- 4GB RAM minimum

### Backend Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Setup lookup tables (first time only)
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
