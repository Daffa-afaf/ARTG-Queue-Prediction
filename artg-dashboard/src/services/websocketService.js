import { io } from 'socket.io-client';

class WebSocketService {
  constructor() {
    console.log('WebSocketService constructor - version dengan batch processing');
    this.externalSocket = null;  // Koneksi ke server WebSocket eksternal
    this.flaskSocket = null;     // Koneksi ke backend Flask
    this.isConnected = false;
  }

  /**
   * Hubungkan ke server WebSocket eksternal dan backend Flask
   * @param {string} externalUrl - URL server eksternal (default: 10.130.0.176)
   * @param {string} flaskUrl - URL backend Flask (default: http://10.5.11.242:5000)
   */
  connect(externalUrl = 'http://10.130.0.176', flaskUrl = 'http://10.5.11.242:5000') {
    // Koneksi ke server WebSocket eksternal
    this.connectToExternalServer(externalUrl);
    
    // Koneksi ke backend Flask
    this.connectToFlaskBackend(flaskUrl);
  }

  /**
   * Koneksi ke server WebSocket eksternal untuk event GATE_IN
   */
  connectToExternalServer(url = 'http://10.130.0.176') {
    if (this.externalSocket) {
      console.log('External socket sudah terhubung');
      return;
    }

    console.log('Connecting to external WebSocket server:', url);

    this.externalSocket = io(url, {
      transports: ['websocket'],   // Hanya websocket
      query: { dashboard: 'true'}, // Identitas sebagai dashboard
      reconnection: true,          // Auto-reconnect jika putus
      reconnectionDelay: 1000,     // Tunggu 1 detik sebelum retry
      reconnectionAttempts: 5,     // Coba reconnect maksimal 5 kali
    });

    // Handler event untuk server eksternal
    this.externalSocket.on('connect', () => {
      this.isConnected = true;
      console.log('Connected to external WebSocket server');
      console.log('External Socket ID:', this.externalSocket.id);
      
      // Meminta state awal yang tersimpan
      this.externalSocket.emit('REQUEST_INITIAL_STATE', {
        eventNames: ['GATE_IN']
      });
      console.log('Requested initial state for GATE_IN events');
    });

    this.externalSocket.on('disconnect', (reason) => {
      console.log('Disconnected from external server:', reason);
    });

    this.externalSocket.on('connect_error', (error) => {
      console.error('External server connection error:', error.message);
    });

    this.externalSocket.on('reconnect_attempt', (attemptNumber) => {
      console.log(`External server reconnection attempt ${attemptNumber}...`);
    });

    this.externalSocket.on('reconnect', (attemptNumber) => {
      console.log(`Reconnected to external server after ${attemptNumber} attempts`);
    });
  }

  /**
   * Koneksi ke backend Flask untuk prediksi
   */
  connectToFlaskBackend(url = 'http://localhost:5000') {
    if (this.flaskSocket) {
      console.log('Flask socket sudah terhubung');
      return;
    }

    console.log('Connecting to Flask backend:', url);

    this.flaskSocket = io(url, {
      transports: ['websocket', 'polling'],
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionDelayMax: 5000,
      reconnectionAttempts: 5,
    });

    // Handler event untuk Flask
    this.flaskSocket.on('connect', () => {
      console.log('Connected to Flask backend');
      console.log('Flask Socket ID:', this.flaskSocket.id);
    });

    this.flaskSocket.on('connection_response', (data) => {
      console.log('Flask backend info:', data);
    });

    this.flaskSocket.on('disconnect', (reason) => {
      console.log('Disconnected from Flask backend:', reason);
    });

    this.flaskSocket.on('connect_error', (error) => {
      console.error('Flask connection error:', error.message);
    });

    this.flaskSocket.on('reconnect_attempt', (attemptNumber) => {
      console.log(`Flask reconnection attempt ${attemptNumber}...`);
    });

    this.flaskSocket.on('reconnect', (attemptNumber) => {
      console.log(`Reconnected to Flask after ${attemptNumber} attempts`);
    });

    this.flaskSocket.on('reconnect_failed', () => {
      console.error('Flask reconnection failed');
    });
  }

  /**
   * Meminta state awal/data historis dari server WebSocket eksternal
   * @param {Array<string>} eventNames - Daftar event yang diminta (mis. ['Gate In'])
   */
  requestInitialState(eventNames = ['Gate In']) {
    if (!this.externalSocket) {
      console.error('External socket belum diinisialisasi. Panggil connect() dahulu.');
      return;
    }

    console.log('Requesting initial state for:', eventNames);
    this.externalSocket.emit('REQUEST_INITIAL_STATE', { eventNames });
  }

  /**
   * Mendengarkan event GATE_IN dari server WebSocket eksternal
   * @param {Function} callback - Fungsi yang dipanggil saat truk datang
   */
  onGateIn(callback) {
    if (!this.externalSocket) {
      console.error('External socket belum diinisialisasi. Panggil connect() dahulu.');
      return;
    }

    this.externalSocket.on('GATE_IN', (data) => {
      console.log('Truck arrived (GATE_IN):', data);
      
      // Server eksternal mengirim data batch: {eventName, data: Array, rowCount, timestamp}
      if (data.data && Array.isArray(data.data)) {
        console.log(`Processing batch of ${data.data.length} trucks`);
        
        // Log struktur penuh truk pertama untuk debugging
        const firstTruck = data.data[0];
        console.log('='.repeat(80));
        console.log('FULL FIRST TRUCK DATA STRUCTURE:');
        console.log('='.repeat(80));
        console.log('Type:', typeof firstTruck);
        console.log('Keys:', Object.keys(firstTruck));
        console.log('\nFULL DATA DUMP (first truck):');
        console.log(JSON.stringify(firstTruck, null, 2));
        console.log('='.repeat(80));
        
        // Proses setiap truk dalam array
        data.data.forEach((truck, index) => {
          callback({data: truck});
        });
      } else {
        // Data truk tunggal
        callback(data);
      }
    });
  }

  /**
   * Kirim data truk ke backend Flask untuk prediksi
   * @param {Object} truckData - Detail truk (truck_id, container_size, dll.)
   */
  sendToPrediction(truckData) {
    if (!this.flaskSocket) {
      console.error('Flask socket belum diinisialisasi. Panggil connect() dahulu.');
      return;
    }

    if (!this.flaskSocket.connected) {
      console.error('Flask socket belum terhubung. Tunggu koneksi.');
      return;
    }

    console.log('Sending truck data to Flask for prediction:', truckData);
    this.flaskSocket.emit('GATE_IN_DATA', truckData);
  }

  /**
   * Mendengarkan hasil prediksi dari backend Flask
   * @param {Function} callback - Fungsi yang dipanggil saat prediksi datang
   */
  onPredictionResult(callback) {
    if (!this.flaskSocket) {
      console.error('Flask socket belum diinisialisasi. Panggil connect() dahulu.');
      return;
    }

    this.flaskSocket.on('PREDICTION_RESULT', (data) => {
      console.log('Prediction received:', data);
      callback(data);
    });
  }

  /**
   * Mendengarkan error prediksi dari backend Flask
   * @param {Function} callback - Fungsi yang dipanggil saat error terjadi
   */
  onPredictionError(callback) {
    if (!this.flaskSocket) {
      console.error('Flask socket belum diinisialisasi. Panggil connect() dahulu.');
      return;
    }

    this.flaskSocket.on('PREDICTION_ERROR', (data) => {
      console.error('Prediction error:', data);
      callback(data);
    });
  }

  /**
   * Mendengarkan rejected prediksi dari backend Flask (duplicate truck)
   * @param {Function} callback - Fungsi yang dipanggil saat prediksi ditolak
   */
  onPredictionRejected(callback) {
    if (!this.flaskSocket) {
      console.error('Flask socket belum diinisialisasi. Panggil connect() dahulu.');
      return;
    }

    this.flaskSocket.on('PREDICTION_REJECTED', (data) => {
      console.log('Prediction rejected (duplicate truck):', data);
      callback(data);
    });
  }

  /**
   * Listener generik (untuk kedua socket)
   * @param {string} eventName - Nama event yang didengar
   * @param {Function} callback - Fungsi yang dipanggil saat event terjadi
   */
  on(eventName, callback) {
    // Coba Flask socket dulu (untuk event connect/disconnect/prediction)
    if (this.flaskSocket) {
      this.flaskSocket.on(eventName, callback);
    } else if (this.externalSocket) {
      this.externalSocket.on(eventName, callback);
    } else {
      console.error('Tidak ada socket yang diinisialisasi. Panggil connect() dahulu.');
    }
  }

  /**
   * Menghapus event listener
   * @param {string} eventName - Nama event yang akan dihapus listener-nya
   * @param {Function} callback - Callback spesifik yang dihapus
   */
  off(eventName, callback) {
    if (this.flaskSocket) {
      this.flaskSocket.off(eventName, callback);
    }
    if (this.externalSocket) {
      this.externalSocket.off(eventName, callback);
    }
  }

  /**
   * Emitter generik
   * @param {string} eventName - Nama event yang dikirim
   * @param {*} data - Data yang dikirim bersama event
   */
  emit(eventName, data) {
    if (this.flaskSocket && this.flaskSocket.connected) {
      this.flaskSocket.emit(eventName, data);
    }
  }

  /**
   * Get connection status
   */
  getConnectionStatus() {
    return this.isConnected;
  }
}

const websocketServiceInstance = new WebSocketService();
export default websocketServiceInstance;
