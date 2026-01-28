# Contributing Guidelines

## 📋 Untuk Developer Internal

Terima kasih telah berkontribusi pada ARTG Queue Prediction System!

### 🔧 Development Setup

1. **Fork & Clone**
   ```bash
   git clone <your-fork-url>
   cd Project1-Magang
   ```

2. **Setup Environment**
   ```bash
   # Backend
   pip install -r requirements.txt
   
   # Frontend
   cd artg-dashboard
   npm install
   ```

3. **Create Branch**
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/bug-description
   ```

### 📝 Coding Standards

#### Python (Backend)
- Follow PEP 8 style guide
- Add docstrings untuk semua fungsi
- Gunakan type hints where applicable
- Maximum line length: 100 characters

```python
def predict_duration(truck_data: dict) -> float:
    """
    Prediksi durasi pemrosesan truk.
    
    Args:
        truck_data: Dictionary berisi info truk (slot, row, tier, dll)
    
    Returns:
        Prediksi durasi dalam menit
    """
    pass
```

#### JavaScript/React (Frontend)
- Use ES6+ features
- Functional components with hooks
- PropTypes untuk type checking
- Consistent naming: camelCase

```javascript
const RealTimeQueue = () => {
  const [trucks, setTrucks] = useState([]);
  // ...
};
```

### 🧪 Testing

Before submitting PR:

1. **Test Backend**
   ```bash
   python App.py
   # Verify API endpoints work
   curl http://localhost:5000/
   ```

2. **Test Frontend**
   ```bash
   cd artg-dashboard
   npm start
   # Test both Batch and Real-time modes
   ```

3. **Test Model Predictions**
   - Add test truck in Batch mode
   - Verify prediction < 100ms
   - Check accuracy within expected range

### 📊 Model Updates

Jika update model:

1. **Retrain dengan data baru**
   - Run cleaning → EDA → modeling notebooks
   - Save baru models ke `models/`
   
2. **Update lookup tables**
   ```bash
   python generate_lookups.py
   ```

3. **Dokumentasi perubahan**
   - Update `model_metadata_2_bulan.json`
   - Catat MAE, RMSE, R² di CHANGELOG.md

4. **Backward compatibility**
   - Pastikan features order sama
   - Test dengan old data format

### 🔍 Pull Request Process

1. **Update dokumentasi** jika perlu
2. **Add/update tests** untuk perubahan Anda
3. **Run full test** sebelum submit
4. **Write clear PR description**:
   ```markdown
   ## Perubahan
   - Apa yang diubah
   - Kenapa perubahan ini perlu
   
   ## Testing
   - Bagaimana di-test
   - Screenshot jika UI changes
   
   ## Checklist
   - [ ] Backend tests pass
   - [ ] Frontend tests pass
   - [ ] Documentation updated
   - [ ] Model backward compatible
   ```

### 🚀 Release Process

1. Update version di:
   - `README.md`
   - `package.json`
   - `App.py` (version string)

2. Update CHANGELOG.md

3. Tag release:
   ```bash
   git tag -a v2.1.0 -m "Release version 2.1.0"
   git push origin v2.1.0
   ```

### ❓ Questions?

Contact maintainer: [email Anda]
