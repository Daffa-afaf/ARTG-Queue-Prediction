# Project Flowchart & Architecture

## Machine Learning Development Flow

```mermaid
graph TD
    A[Raw Data<br/>gatein_out_2bulan.csv<br/>150k+ records] --> B[Data Cleaning<br/>cleaning_raw_data2bulan_NEW.ipynb]
    
    B --> C[Cleaned Data<br/>dataset_rapi_2bulan.csv<br/>105,995 records]
    
    C --> D[EDA & Feature Engineering<br/>eda_feature_engineering2bulan.ipynb]
    
    D --> E[Final Dataset<br/>dataset_final2bulan_45FEATURES_PROPER.csv<br/>96,000 records × 45 features]
    
    E --> F[Model Training & Tuning<br/>modeling_45features_PROPER_FIXED.ipynb]
    
    F --> G{Model Comparison}
    
    G --> H[LightGBM<br/>MAE: 6.31]
    G --> I[XGBoost<br/>MAE: 6.45]
    G --> J[CatBoost<br/>MAE: 6.38]
    G --> K[Random Forest<br/>MAE: 6.89]
    G --> L[Gradient Boosting<br/>MAE: 6.72]
    G --> M[Stacking Ensemble ⭐<br/>MAE: 6.25]
    G --> N[Voting Ensemble<br/>MAE: 6.34]
    
    M --> O[Best Model Selected]
    
    O --> P[Save Artifacts]
    P --> Q[best_model_2_bulan.pkl]
    P --> R[label_encoders_2_bulan.pkl]
    P --> S[features_list_2_bulan.pkl]
    P --> T[lookup_tables_2buban.pkl]
    P --> U[model_metadata_2_bulan.json]
    
    E --> V[generate_lookups.py]
    V --> T
    
    style M fill:#FF69B4
    style O fill:#FF8C00
```

## System Architecture Flow

```mermaid
graph LR
    A[External WebSocket<br/>Server<br/>10.130.0.176] -->|GATE_IN Events| B[React Frontend<br/>Port 3000]
    
    B <-->|Socket.io| C[Flask Backend<br/>Port 5000]
    
    C --> D{Feature<br/>Engineering}
    
    D --> E[45 Features Generated]
    
    E --> F[ML Ensemble Model]
    
    F -->|Prediction| G[Duration<br/>6-30 min]
    
    G --> C
    C -->|Result| B
    
    B --> H[Queue Display<br/>CY1-CY6, D1]
    
    C --> I[(Lookup Tables)]
    C --> J[(Label Encoders)]
    C --> K[(Queue Cache<br/>TTL 60s)]
    
    style F fill:#9370DB
    style G fill:#FF69B4
    style H fill:#FF8C00
```

## Real-Time Prediction Flow

```mermaid
sequenceDiagram
    participant ES as External Server<br/>(10.130.0.176)
    participant FE as React Frontend
    participant BE as Flask Backend
    participant ML as ML Model
    participant Q as Queue Management
    
    ES->>FE: GATE_IN Event<br/>(truck data)
    
    Note over FE: Validate Data<br/>• slot/row/tier exist?<br/>• block-tier valid?
    
    alt Data Valid
        FE->>BE: GATE_IN_DATA<br/>(WebSocket)
        
        Note over BE: Deduplication Check<br/>truck_id + gate_in_time
        
        alt Not Duplicate
            BE->>BE: Feature Engineering<br/>(45 features)
            BE->>ML: Predict Duration
            ML-->>BE: Prediction (6-30 min)
            BE->>Q: Add to Queue
            BE->>FE: PREDICTION_RESULT
            FE->>FE: Update UI
        else Duplicate
            BE->>BE: Skip Processing
        end
        
    else Data Invalid
        FE->>FE: Reject & Log Warning<br/>(no prediction)
    end
```

## Data Transformation Pipeline

```mermaid
graph TD
    A[Raw Truck Data] --> B{Validation}
    
    B -->|Pass| C[Feature Engineering Pipeline]
    B -->|Fail| Z[Reject]
    
    C --> D[1. Categorical Cleaning]
    D --> E[2. Temporal Features<br/>hour, day, shift, weekend]
    E --> F[3. Location Features<br/>distance, vertical_distance]
    F --> G[4. Historical Averages<br/>slot, tier, location, hour]
    G --> H[5. Container Features<br/>size, type, status]
    H --> I[6. Congestion Features<br/>hourly_volume, count]
    I --> J[7. Interaction Features<br/>slot×tier, size×tier]
    J --> K[8. Statistical Features<br/>std, min, max]
    K --> L[9. Lag Features<br/>prev_duration, rolling_mean]
    L --> M[10. Target Encoding<br/>block, location]
    
    M --> N[45 Features Complete]
    N --> O[Label Encode<br/>Categorical → Numeric]
    O --> P[ML Model Input]
    P --> Q[Prediction Output]
    
    style N fill:#FF69B4
    style Q fill:#FF8C00
```

## Feature Importance Breakdown

```mermaid
graph LR
    A[45 Features] --> B[Lag Features<br/>31%]
    A --> C[Historical Avg<br/>25%]
    A --> D[Location<br/>18%]
    A --> E[Congestion<br/>12%]
    A --> F[Others<br/>14%]
    
    B --> B1[prev_duration: 16.8%]
    B --> B2[rolling_mean_3: 14.2%]
    
    C --> C1[lokasi_historical_avg: 11.5%]
    C --> C2[slot_historical_avg: 9.3%]
    C --> C3[Others: 4.2%]
    
    D --> D1[distance_from_gate: 7.8%]
    D --> D2[tier_numeric: 4.8%]
    D --> D3[Others: 5.4%]
    
    E --> E1[congestion_count: 6.4%]
    E --> E2[hourly_volume: 5.6%]
    
    style B fill:#FF8C00
    style C fill:#9370DB
```

## Development Workflow

```mermaid
graph TD
    A[New Data Available] --> B{Need Retraining?}
    
    B -->|Yes| C[Update Raw Data]
    C --> D[Run Cleaning Notebook]
    D --> E[Run EDA Notebook]
    E --> F[Run Modeling Notebook]
    F --> G[Generate Lookup Tables]
    G --> H[Test New Model]
    
    H --> I{Performance<br/>Improved?}
    
    I -->|Yes| J[Deploy to Production]
    I -->|No| K[Tune Hyperparameters]
    K --> F
    
    J --> L[Update Version]
    L --> M[Document Changes]
    M --> N[Git Tag Release]
    
    B -->|No| O[Continue with<br/>Current Model]
    
    style J fill:#FF69B4
    style O fill:#FF8C00
```

## Data Validation Flow

```mermaid
graph TD
    A[Truck Data Received] --> B{slot exists?}
    B -->|No| Z1[❌ REJECT<br/>Incomplete Location]
    B -->|Yes| C{row exists?}
    C -->|No| Z1
    C -->|Yes| D{tier exists?}
    D -->|No| Z1
    D -->|Yes| E{block == 7?}
    
    E -->|Yes| F{tier == 'D1'?}
    F -->|No| Z2[❌ REJECT<br/>Invalid Tier for D1]
    F -->|Yes| G[✅ Valid]
    
    E -->|No| G
    
    G --> H{In Cache?}
    H -->|Yes| Z3[⚠️ SKIP<br/>Duplicate]
    H -->|No| I[Add to Cache]
    I --> J[✅ Process]
    
    J --> K[Feature Engineering]
    K --> L[ML Prediction]
    L --> M[Add to Queue]
    
    style G fill:#FF69B4
    style J fill:#FF69B4
    style M fill:#FF8C00
    style Z1 fill:#FF6B6B
    style Z2 fill:#FF6B6B
    style Z3 fill:#FFA500
```

---

## Application Modes (Same Model, Different Input)

```mermaid
graph LR
    A[Stacking Ensemble Model<br/>MAE: 6.25 min<br/>45 Features] --> B[Batch Mode]
    A --> C[Real-Time Mode]
    
    B --> B1[Manual Input Form]
    B1 --> B2[Use: Offline Testing]
    B2 --> B3[No WiFi Required]
    B3 --> D[Prediction Result]
    
    C --> C1[WebSocket Feed]
    C1 --> C2[Use: Live Monitoring]
    C2 --> C3[WiFi 10.130.0.176]
    C3 --> D
    
    style A fill:#9370DB
    style B fill:#FF69B4
    style C fill:#FF8C00
    style D fill:#FF6B6B
```

---

## Model Comparison During Training

During the modeling phase, 7 algorithms were compared. Only the **Stacking Ensemble** was deployed to production.

```
┌─────────────────────┬──────────┬────────────┐
│ Algorithm           │ MAE      │ Status     │
├─────────────────────┼──────────┼────────────┤
│ Stacking Ensemble ⭐│ 6.25 min │ DEPLOYED   │
│ LightGBM            │ 6.31 min │ Comparison │
│ Voting Ensemble     │ 6.34 min │ Comparison │
│ CatBoost            │ 6.38 min │ Comparison │
│ XGBoost             │ 6.45 min │ Comparison │
│ Gradient Boosting   │ 6.72 min │ Comparison │
│ Random Forest       │ 6.89 min │ Comparison │
└─────────────────────┴──────────┴────────────┘

✅ Production Model: Stacking Ensemble only
📊 Training Data: 96,000 records × 45 features
```

---
