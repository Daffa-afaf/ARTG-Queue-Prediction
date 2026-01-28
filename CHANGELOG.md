# Changelog

All notable changes to ARTG Queue Prediction System will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [2.0.0] - 2026-01-28

### ✨ Added
- **Stacking Ensemble Model**: LightGBM + XGBoost + CatBoost + Ridge
  - MAE improved from 7.2 to 6.25 minutes
  - 51.2% error reduction vs baseline
  - 82% predictions within 10 minutes
- **Real-time WebSocket Integration**
  - External server connection (10.130.0.176)
  - Auto-prediction for incoming trucks
  - Deduplication cache (TTL 60s)
- **Dual Mode Operation**
  - Batch Mode: Manual truck input
  - Real-time Mode: Live queue streaming
- **45 Engineered Features** (vs 42 in V1)
  - Added lag features (prev_duration, rolling_mean_3)
  - Enhanced interaction features
  - Target encoding for block/location
- **Strict Data Validation**
  - Mandatory slot/row/tier (no fallback)
  - Block-tier compatibility check
  - D1 block strict validation
- **React Dashboard UI/UX**
  - Tailwind CSS styling
  - Block selection tabs
  - Real-time statistics
  - Truck status indicators

### 🔧 Changed
- Shift system: 8 shifts (3-hour intervals) instead of 6
- Outlier removal: Q5-Q99 (vs Q10-Q90)
- Feature engineering pipeline refactored
- Model training with Optuna (50 trials per model)
- Lookup tables generation script improved

### 🐛 Fixed
- Duplicate prediction issue in real-time mode
- Block 7 vs D1 confusion
- WebSocket reconnection handling
- Feature order consistency training vs production
- Categorical value cleaning (.0 removal)

### 📊 Performance
- Training dataset: 96,000 records (2 months)
- Test MAE: 6.25 minutes
- Test RMSE: 8.47 minutes
- Test R²: 0.726
- Inference time: < 100ms per truck

---

## [1.0.0] - 2025-12-15 (Initial Release)

### ✨ Added
- Basic ML prediction model (Random Forest)
- Flask backend API
- React frontend (basic UI)
- 42 engineered features
- Batch mode operation only
- Model training notebooks
- Data cleaning pipeline

### 📊 Performance
- Training dataset: 80,000 records
- Test MAE: 7.2 minutes
- Test R²: 0.68

---

## [Unreleased]

### 🚀 Planned Features
- [ ] Database persistence (PostgreSQL)
- [ ] Redis cache for distributed systems
- [ ] Authentication & authorization
- [ ] REST API fallback
- [ ] A/B testing framework
- [ ] Auto-retraining pipeline
- [ ] Monitoring dashboard (Grafana)
- [ ] Historical queue analytics
- [ ] Export reports (PDF/Excel)
- [ ] Mobile-responsive UI
- [ ] Multi-language support
- [ ] Email/SMS notifications

---

## Version History Summary

| Version | Date       | MAE (min) | Features | Mode          |
|---------|------------|-----------|----------|---------------|
| 2.0.0   | 2026-01-28 | 6.25      | 45       | Batch + RT    |
| 1.0.0   | 2025-12-15 | 7.2       | 42       | Batch only    |
