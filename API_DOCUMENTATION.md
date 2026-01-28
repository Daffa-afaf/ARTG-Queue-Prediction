# 📡 API Documentation

## Base URL
```
Production:  http://10.5.11.242:5000
Development: http://localhost:5000
```

---

## 🔍 REST API Endpoints

### 1. Health Check

**Endpoint:** `GET /`

**Description:** Cek status server dan konfigurasi model

**Response:**
```json
{
  "status": "running",
  "service": "ARTG Multi-Block Queue Management",
  "model": "Stacking Ensemble",
  "features": 45,
  "shift_type": "8_shifts_3h",
  "blocks": 7,
  "version": "2.0"
}
```

**Example:**
```bash
curl http://localhost:5000/
```

---

### 2. Get All Blocks

**Endpoint:** `GET /blocks`

**Description:** Mengambil data semua blok beserta antrian

**Response:**
```json
{
  "1": {
    "name": "CY1",
    "queue": [
      {
        "truck_id": "B9087JB",
        "lokasi": "30 1 2",
        "block": "1G",
        "container_size": "40",
        "container_type": "DRY",
        "ctr_status": "FULL",
        "job_type": "EXPORT",
        "gate_in_time": "2026-01-28T13:15:00",
        "predicted_duration": 18.45,
        "status": "predicted"
      }
    ],
    "queue_length": 1
  },
  "2": {
    "name": "CY2",
    "queue": [...],
    "queue_length": 15
  },
  ...
}
```

**Example:**
```bash
curl http://localhost:5000/blocks
```

---

### 3. Get Block Statistics

**Endpoint:** `GET /blocks/<block_id>/stats`

**Description:** Mengambil statistik untuk blok tertentu

**Parameters:**
- `block_id` (path): Integer 1-7 (1=CY1, 2=CY2, ..., 7=D1)

**Response:**
```json
{
  "count": 15,
  "avg_duration": 18.45,
  "total_duration": 276.75,
  "min_duration": 12.30,
  "max_duration": 28.90
}
```

**Example:**
```bash
curl http://localhost:5000/blocks/2/stats
```

**Error Response (Invalid Block):**
```json
{
  "error": "Invalid block ID (must be 1-7)"
}
```
HTTP Status: `400`

---

### 4. Get Global Statistics

**Endpoint:** `GET /stats`

**Description:** Mengambil statistik gabungan seluruh blok

**Response:**
```json
{
  "total_trucks": 47,
  "avg_duration": 19.32,
  "total_duration": 908.04,
  "blocks_with_trucks": 6
}
```

**Example:**
```bash
curl http://localhost:5000/stats
```

---

### 5. Add Truck (Batch Mode)

**Endpoint:** `POST /blocks/<block_id>/add_truck`

**Description:** Menambahkan truk ke antrian dan memprediksi durasi

**Parameters:**
- `block_id` (path): Integer 1-7

**Request Body:**
```json
{
  "truck_id": "T12345",
  "slot": "30",
  "row": "1",
  "tier": "2",
  "block": "1G",
  "job_type": "DELIVERY",
  "container_size": "40",
  "container_type": "DRY",
  "ctr_status": "FULL"
}
```

**Response:**
```json
{
  "message": "Truck added and predicted",
  "truck": {
    "truck_id": "T12345",
    "lokasi": "30 1 2",
    "block": "1G",
    "container_size": "40",
    "container_type": "DRY",
    "ctr_status": "FULL",
    "job_type": "EXPORT",
    "gate_in_time": "2026-01-28T10:30:15",
    "predicted_duration": 18.45,
    "status": "predicted"
  }
}
```

**Example:**
```bash
curl -X POST http://localhost:5000/blocks/1/add_truck \
  -H "Content-Type: application/json" \
  -d '{
    "truck_id": "T12345",
    "slot": "30",
    "row": "1",
    "tier": "2",
    "block": "1G",
    "job_type": "DELIVERY",
    "container_size": "40",
    "container_type": "DRY",
    "ctr_status": "FULL"
  }'
```

**Error Response (Invalid Block):**
```json
{
  "error": "Invalid block ID"
}
```
HTTP Status: `400`

**Error Response (Validation Failed):**
```json
{
  "error": "Stack '2' tidak diizinkan untuk block D1. Block ini hanya menerima stack: D1"
}
```
HTTP Status: `400`

---

### 6. Remove Truck

**Endpoint:** `DELETE /blocks/<block_id>/trucks/<truck_id>`

**Description:** Menghapus truk dari antrian

**Parameters:**
- `block_id` (path): Integer 1-7
- `truck_id` (path): String truck ID

**Response:**
```json
{
  "message": "Truck T12345 removed from block CY1"
}
```

**Error Response (Not Found):**
```json
{
  "error": "Truck not found in queue"
}
```
HTTP Status: `404`

---

### 7. Clear Block Queue

**Endpoint:** `POST /blocks/<block_id>/clear`

**Description:** Menghapus semua truk dari antrian blok

**Parameters:**
- `block_id` (path): Integer 1-7

**Response:**
```json
{
  "message": "Queue cleared for block CY2",
  "removed_count": 15
}
```

---

### 8. Load Demo Data

**Endpoint:** `POST /demo/populate`

**Description:** Populate antrian dengan data demo (untuk testing)

**Response:**
```json
{
  "message": "Demo data loaded",
  "trucks_added": 25,
  "blocks_populated": [1, 2, 3, 4, 5, 6, 7]
}
```

---

## 📡 WebSocket Events

### Connection

**URL:** `ws://localhost:5000`

**Client Connection:**
```javascript
import { io } from 'socket.io-client';

const socket = io('http://localhost:5000', {
  transports: ['websocket', 'polling'],
  reconnection: true
});

socket.on('connect', () => {
  console.log('Connected to Flask backend');
  console.log('Socket ID:', socket.id);
});
```

---

### Event: Connection Response

**Direction:** Server → Client

**Event Name:** `connection_response`

**Payload:**
```json
{
  "status": "connected",
  "message": "Connected to Flask backend",
  "socket_id": "abc123",
  "server_time": "2026-01-28T10:30:15"
}
```

**Example:**
```javascript
socket.on('connection_response', (data) => {
  console.log('Server says:', data.message);
});
```

---

### Event: Send Truck Data (Real-time Mode)

**Direction:** Client → Server

**Event Name:** `GATE_IN_DATA`

**Payload:**
```json
{
  "truck_id": "B9087JB",
  "gate_in_time": "2026-01-28T13:15:00",
  "container_size": "40",
  "container_type": "DRY",
  "ctr_status": "FCL",
  "slot": 30,
  "row": 1,
  "tier": 1,
  "block": 2,
  "job_type": "EXPORT"
}
```

**Example:**
```javascript
websocketService.sendToPrediction({
  truck_id: "B9087JB",
  gate_in_time: new Date().toISOString(),
  container_size: "40",
  container_type: "DRY",
  ctr_status: "FCL",
  slot: 30,
  row: 1,
  tier: 1,
  block: 2,
  job_type: "EXPORT"
});
```

---

### Event: Prediction Result

**Direction:** Server → Client

**Event Name:** `PREDICTION_RESULT`

**Payload:**
```json
{
  "truck_id": "B9087JB",
  "predicted_duration_minutes": 18.45,
  "expected_ready_time": "2026-01-28T13:33:27",
  "block": 2,
  "block_name": "CY2",
  "status": "success",
  "gate_in_time": "2026-01-28T13:15:00"
}
```

**Example:**
```javascript
socket.on('PREDICTION_RESULT', (data) => {
  console.log(`Truck ${data.truck_id}: ${data.predicted_duration_minutes} min`);
  
  // Update UI
  updateQueueDisplay(data);
});
```

---

### Event: Prediction Error

**Direction:** Server → Client

**Event Name:** `PREDICTION_ERROR`

**Payload:**
```json
{
  "truck_id": "B9087JB",
  "error": "Stack '2' tidak diizinkan untuk block D1",
  "status": "rejected",
  "reason": "validation_failed"
}
```

**Example:**
```javascript
socket.on('PREDICTION_ERROR', (error) => {
  console.error(`Error for truck ${error.truck_id}:`, error.error);
  
  // Show error notification
  showErrorNotification(error);
});
```

---

### Event: Queue Update

**Direction:** Server → Client (Broadcast)

**Event Name:** `QUEUE_UPDATE`

**Payload:**
```json
{
  "block_id": 2,
  "block_name": "CY2",
  "queue_length": 16,
  "avg_duration": 19.32,
  "total_duration": 309.12,
  "timestamp": "2026-01-28T13:15:00"
}
```

**Example:**
```javascript
socket.on('QUEUE_UPDATE', (data) => {
  console.log(`${data.block_name}: ${data.queue_length} trucks`);
  updateStatistics(data);
});
```

---

## 🔐 Error Codes

| HTTP Code | Description |
|-----------|-------------|
| 200 | Success |
| 400 | Bad Request - Invalid input atau validation error |
| 404 | Not Found - Truck atau resource tidak ditemukan |
| 500 | Internal Server Error - Server error atau prediction error |

### Common Error Messages

#### Validation Errors
```json
{
  "error": "Invalid block ID (must be 1-7)"
}
```

```json
{
  "error": "Stack '2' tidak diizinkan untuk block D1. Block ini hanya menerima stack: D1"
}
```

```json
{
  "error": "Missing required fields: slot, row, tier"
}
```

#### Processing Errors
```json
{
  "error": "Prediction failed",
  "details": "Feature engineering error: ...",
  "fallback_used": true,
  "fallback_value": 22.47
}
```

---

## 📊 Data Models

### Truck Object
```typescript
interface Truck {
  truck_id: string;          // Unique truck identifier
  lokasi: string;            // Format: "slot row tier" (e.g., "30 1 2")
  block: string;             // Block name (e.g., "1G", "2A", "D1")
  container_size: string;    // "20" or "40"
  container_type: string;    // "DRY", "REEFER", "OT", "FLAT", etc.
  ctr_status: string;        // "FULL" (FCL) or "EMPTY" (MTY)
  job_type: string;          // "EXPORT" or "IMPORT"
  gate_in_time: string;      // ISO 8601 format
  predicted_duration: number; // Minutes (float)
  status: string;            // "waiting_prediction", "predicted", "processing"
}
```

### Queue Object
```typescript
interface Queue {
  name: string;              // Block name (e.g., "CY1")
  queue: Truck[];            // Array of trucks
  queue_length: number;      // Number of trucks
  total_duration?: number;   // Sum of predicted durations (optional)
}
```

### Statistics Object
```typescript
interface Statistics {
  count: number;             // Number of trucks
  avg_duration: number;      // Average predicted duration
  total_duration: number;    // Sum of all durations
  min_duration?: number;     // Minimum duration (optional)
  max_duration?: number;     // Maximum duration (optional)
}
```

---

## 🧪 Testing Examples

### cURL Examples

```bash
# Health check
curl http://localhost:5000/

# Get all blocks
curl http://localhost:5000/blocks

# Get block 2 stats
curl http://localhost:5000/blocks/2/stats

# Add truck to block 1
curl -X POST http://localhost:5000/blocks/1/add_truck \
  -H "Content-Type: application/json" \
  -d '{
    "truck_id": "TEST001",
    "slot": "30",
    "row": "1",
    "tier": "2",
    "block": "1G",
    "job_type": "DELIVERY",
    "container_size": "40",
    "container_type": "DRY",
    "ctr_status": "FULL"
  }'

# Remove truck
curl -X DELETE http://localhost:5000/blocks/1/trucks/TEST001

# Clear queue
curl -X POST http://localhost:5000/blocks/1/clear

# Load demo data
curl -X POST http://localhost:5000/demo/populate
```

### Python Examples

```python
import requests
import json

BASE_URL = "http://localhost:5000"

# Health check
response = requests.get(f"{BASE_URL}/")
print(response.json())

# Add truck
truck_data = {
    "truck_id": "TEST001",
    "slot": "30",
    "row": "1",
    "tier": "2",
    "block": "1G",
    "job_type": "DELIVERY",
    "container_size": "40",
    "container_type": "DRY",
    "ctr_status": "FULL"
}

response = requests.post(
    f"{BASE_URL}/blocks/1/add_truck",
    json=truck_data,
    headers={"Content-Type": "application/json"}
)

print(response.json())
```

### JavaScript Examples

```javascript
// Fetch blocks
fetch('http://localhost:5000/blocks')
  .then(res => res.json())
  .then(data => console.log(data));

// Add truck
fetch('http://localhost:5000/blocks/1/add_truck', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    truck_id: "TEST001",
    slot: "30",
    row: "1",
    tier: "2",
    block: "1G",
    job_type: "DELIVERY",
    container_size: "40",
    container_type: "DRY",
    ctr_status: "FULL"
  })
})
.then(res => res.json())
.then(data => console.log(data));
```

---

## 📝 Notes

### Field Mappings

**Job Type:**
- Frontend display: `DELIVERY` / `RECEIVING`
- Backend processing: `EXPORT` / `IMPORT`
- Mapping: DELIVERY → EXPORT, RECEIVING → IMPORT

**Block IDs:**
- 1 = CY1
- 2 = CY2
- 3 = CY3
- 4 = CY4
- 5 = CY5
- 6 = CY6
- 7 = D1

**Stack/Tier Validation:**
- CY1-CY6: Any numeric tier accepted (relaxed validation)
- D1 (Block 7): ONLY accepts tier = "D1" (strict validation)

### Timeouts

- HTTP Request: 30 seconds
- WebSocket idle: No timeout (persistent connection)
- Prediction timeout: 5 seconds (fallback to mean if exceeded)

### Rate Limiting

No rate limiting currently implemented. For production, consider:
- Max 100 requests/minute per IP
- Max 1000 WebSocket messages/minute per connection

---

**Last Updated:** 2026-01-28  
**API Version:** 2.0  
**Maintained By:** [Nama Mahasiswa Magang]
