import React, { useState, useEffect, useCallback, useRef } from 'react';
import { Clock, TrendingUp, AlertCircle, Truck, Layers } from 'lucide-react';
import websocketService from '../services/websocketService';

function RealTimeQueue() {
  // Manajemen state (mirip batch mode)
  const [selectedBlock, setSelectedBlock] = useState(1); // blok mana yang sedang dipilih
  const [blocksData, setBlocksData] = useState({}); // menyimpan antrian 7 blok
  const [statistics, setStatistics] = useState({ // jumlah truk, durasi rata-rata, waktu total, waktu bersih
    trucks_in_queue: 0,
    avg_duration: 0,
    total_time: 0,
    clear_time: 0
  });
  const [isConnected, setIsConnected] = useState(false); // status koneksi WebSocket

  // Inisialisasi data blok
  useEffect(() => {
    const initialBlocks = {};
    for (let i = 1; i <= 7; i++) {
      initialBlocks[i] = {
        queue: [],
        queue_length: 0,
        total_duration: 0,
        name: i === 7 ? 'D1' : `CY${i}`
      };
    }
    setBlocksData(initialBlocks);
  }, []);

  // Koneksi WebSocket & event listeners (dengan callback yang stabil)
  const handleConnectionStatus = useCallback((connected) => {
    console.log('Connection status changed:', connected);
    setIsConnected(connected);
  }, []);

  // Lacak truk yang sudah diproses untuk mencegah duplikat dari server eksternal
  const processedTrucksRef = useRef(new Set());
  const cleanupTimerRef = useRef(null);

  // Mulai interval pembersihan saat komponen dimuat
  useEffect(() => {
    // Bersihkan cache setiap 30 detik
    cleanupTimerRef.current = setInterval(() => {
      const cacheSize = processedTrucksRef.current.size;
      if (cacheSize > 0) {
        processedTrucksRef.current.clear();
        console.log(`Cleared ${cacheSize} entries from processed trucks cache`);
      }
    }, 30000);

    // Bersihkan saat komponen di-unmount
    return () => {
      if (cleanupTimerRef.current) {
        clearInterval(cleanupTimerRef.current);
      }
    };
  }, []);

  const handleTruckArrivalCallback = useCallback((data) => {
    console.log('New truck arrival:', data);
    const truck = data.data || data;
    
    // LOG FULL TRUCK DATA untuk debugging - DETAILED VERSION
    console.log('='.repeat(80));
    console.log('FULL TRUCK OBJECT RECEIVED - DETAILED INSPECTION:');
    console.log('='.repeat(80));
    
    // Total fields
    const allKeys = Object.keys(truck);
    console.log(`Total fields: ${allKeys.length}`);
    console.log('');
    
    // List all fields with type and value
    console.log('ALL FIELDS (nama - tipe - nilai):');
    allKeys.forEach((key, index) => {
      const value = truck[key];
      const type = typeof value;
      console.log(`  ${index + 1}. "${key}" (${type}) = ${JSON.stringify(value)}`);
    });
    console.log('');
    
    // Full JSON
    console.log('FULL JSON:');
    console.log(JSON.stringify(truck, null, 2));
    console.log('='.repeat(80));
    
    // Parse field TO_BLOCK (format: "1D", "2A", "3C", dll) untuk ekstrak nomor blok
    const rawToBlock = truck.TO_BLOCK || truck.to_block || '1';
    const toBlockStr = rawToBlock.toString().trim();

    // Normalisasi: jika dimulai dengan D berarti blok D1 (id=7); digit pertama untuk CY1-6
    const isD1Token = toBlockStr.toUpperCase().startsWith('D');
    const blockNum = isD1Token
      ? 7
      : parseInt(toBlockStr.charAt(0), 10) || 1;

    // Label yang ditampilkan di UI: paksa D1 untuk block 7 agar tidak muncul 7A
    const toBlockLabel = blockNum === 7 ? 'D1' : toBlockStr;

    console.log(`Parsed TO_BLOCK "${toBlockStr}" -> Block ${blockNum} (label: ${toBlockLabel})`);

    // Generate ID truk yang unik
    const uniqueId = truck.TRUCK_ID || truck.truck_id || `TRUCK-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    
    // Normalisasi field lokasi dan hapus spasi
    const slotValRaw = (truck.X || truck.SLOT || truck.slot || '').toString().trim();
    const rowValRaw = (truck.Y || truck.ROW || truck.row || '').toString().trim();
    const tierValRaw = (truck.Z || truck.TIER || truck.tier || '').toString().trim();

    // VALIDASI: REJECT truck tanpa lokasi lengkap (tidak ada fallback ke '1')
    if (!slotValRaw || !rowValRaw || !tierValRaw) {
      console.warn(`   REJECTED truck ${uniqueId}: incomplete location data`);
      console.warn(`   Slot: '${slotValRaw}', Row: '${rowValRaw}', Tier: '${tierValRaw}'`);
      console.warn(`   Reason: All location fields (slot, row, tier) must be provided`);
      return; // Jangan proses truck ini sama sekali
    }

    // Gunakan nilai asli tanpa fallback
    const slotVal = slotValRaw;
    const rowVal = rowValRaw;
    const tierVal = tierValRaw;

    // Jika target block adalah D1 (7) tapi tier bukan D1, tolak di frontend agar tidak tampil/terproses
    if (blockNum === 7 && tierVal.toUpperCase() !== 'D1') {
      console.warn(`Rejecting truck ${uniqueId} at frontend: block D1 requires tier D1, got "${tierVal}"`);
      return;
    }

    const slotNum = parseInt(slotVal, 10) || 1;
    const rowNum = parseInt(rowVal, 10) || 1;
    const tierNum = parseInt(tierVal, 10) || 1;

    const gateInTime = (truck.GATE_IN_TIME || truck.gate_in_time || '').toString().trim() || new Date().toISOString();
    const dedupKey = `${uniqueId}_${gateInTime}`;

    // CEGAH DUPLIKAT: Cek apakah truck_id sudah diproses dalam batch ini
    if (processedTrucksRef.current.has(dedupKey)) {
      console.log(`Skipping duplicate: ${uniqueId}`);
      return;
    }

    // Tandai truk sebagai sudah diproses
    processedTrucksRef.current.add(dedupKey);
    console.log(`Registered truck: ${uniqueId} (cache: ${processedTrucksRef.current.size}`);

    // job_type disimpan untuk ke backend (EXPORT/IMPORT), display_job_type untuk UI (DELIVERY/RECEIVING)
    const backendJobType = truck.ACTIVITY === 'DELIVERY' ? 'EXPORT' : 'IMPORT';
    const displayJobType = (truck.ACTIVITY || '').toUpperCase() === 'DELIVERY'
      ? 'DELIVERY'
      : 'RECEIVING';

    const truckRecord = {
      truck_id: uniqueId,
      // Map UPPER_CASE fields dari server eksternal
      container_no: truck.CONTAINER_NO || 'N/A',
      idle_gate: parseInt(truck.IDLE_GATE) || 0,
      idle_waiting: parseInt(truck.IDLE_WAITING) || 0,
      truck_location: truck.TRUCK_LOCATION || 'UNKNOWN',
      to_block: toBlockLabel,
      activity: truck.ACTIVITY || 'UNKNOWN',
      // Pisahkan istilah UI dan istilah untuk model
      job_type: backendJobType,
      display_job_type: displayJobType,
      container_size: truck.CTR_SIZE || truck.CONTAINER_SIZE || truck.container_size || 40,
      container_type: truck.CTR_TYPE || truck.CONTAINER_TYPE || truck.container_type || 'DRY',
      ctr_status: truck.CTR_STATUS || truck.ctr_status || 'FCL',
      gate_in_time: gateInTime,
      lokasi: `${slotNum} ${rowNum} ${tierNum}`,
      block: blockNum,
      expected_ready_time: null,
      predicted_duration: null,
      status: 'waiting_prediction'
    };

    // Cek apakah truk sudah ada di antrian (cegah duplikat)
    setBlocksData(prev => {
      const newBlocks = { ...prev };
      if (!newBlocks[blockNum]) {
        newBlocks[blockNum] = { queue: [], queue_length: 0, total_duration: 0 };
      }
      
      // Cek truk yang sudah ada dengan ID yang sama
      const existingIndex = newBlocks[blockNum].queue.findIndex(t => t.truck_id === uniqueId);
      if (existingIndex !== -1) {
        console.log('Duplicate truck ignored:', uniqueId);
        return prev;
      }
      
      newBlocks[blockNum] = {
        ...newBlocks[blockNum],
        queue: [...newBlocks[blockNum].queue, truckRecord],
        queue_length: newBlocks[blockNum].queue_length + 1
      };
      
      return newBlocks;
    });

    websocketService.sendToPrediction({
        truck_id: truckRecord.truck_id,
        gate_in_time: truckRecord.gate_in_time,
        container_size: truckRecord.container_size,
        container_type: truckRecord.container_type,
        ctr_status: truckRecord.ctr_status,
        slot: slotNum,
        row: rowNum,
        tier: tierNum,
        block: blockNum,
        job_type: truckRecord.job_type
    });
  }, []);

  const handlePredictionResultCallback = useCallback((result) => {
    console.log('Prediction received:', result);
    
    setBlocksData(prev => {
      const newBlocks = { ...prev };
      
      for (const blockNum in newBlocks) {
        const block = newBlocks[blockNum];
        const truckIndex = block.queue.findIndex(t => t.truck_id === result.truck_id);
        
        if (truckIndex !== -1) {
          const truck = block.queue[truckIndex];
          
          if (truck.status === 'predicted') {
            console.log('Duplicate prediction ignored for', truck.truck_id);
            return prev;
          }
          
          const duration = result.predicted_duration_minutes;
          const gateIn = new Date(truck.gate_in_time);
          const expectedReady = new Date(gateIn.getTime() + duration * 60000);
          
          block.queue[truckIndex] = {
            ...truck,
            predicted_duration: duration,
            expected_ready_time: expectedReady.toISOString(),
            status: 'predicted'
          };
          
          block.total_duration += duration;
          break;
        }
      }
      
      return newBlocks;
    });
  }, []);

  useEffect(() => {
    console.log('Real-time mode: Connecting to Flask backend...');
    
    websocketService.connect();
    
    // Cek apakah sudah terhubung dan sinkronkan state
    if (websocketService.getConnectionStatus()) {
      console.log('Already connected, syncing state...');
      setIsConnected(true);
    }

    const connectHandler = () => {
      console.log('Connected to Flask backend');
      handleConnectionStatus(true);
    };

    const disconnectHandler = () => {
      console.log('Disconnected from Flask backend');
      handleConnectionStatus(false);
    };

    const errorHandler = (error) => {
      console.error('PREDICTION_ERROR received:', error);
      // Jika error karena block rejected, hapus truck tsb dari queue
      if (error && error.truck_id) {
        setBlocksData(prevData => {
          const updatedData = { ...prevData };
          // Cek semua blok untuk truck yang di-reject
          for (let blockNum = 1; blockNum <= 7; blockNum++) {
            if (updatedData[blockNum] && updatedData[blockNum].queue) {
              updatedData[blockNum].queue = updatedData[blockNum].queue.filter(
                truck => truck.truck_id !== error.truck_id
              );
              updatedData[blockNum].queue_length = updatedData[blockNum].queue.length;
            }
          }
          console.log(`Removed truck ${error.truck_id} from all queues`);
          return updatedData;
        });
      }
    };

    // Handler untuk prediksi yang ditolak (mis. stack tidak valid untuk blok)
    const rejectionHandler = (rej) => {
      if (!rej || !rej.truck_id) return;
      console.warn('PREDICTION_REJECTED received:', rej);
      setBlocksData(prevData => {
        const updatedData = { ...prevData };
        for (let blockNum = 1; blockNum <= 7; blockNum++) {
          if (updatedData[blockNum] && updatedData[blockNum].queue) {
            updatedData[blockNum].queue = updatedData[blockNum].queue.filter(
              truck => truck.truck_id !== rej.truck_id
            );
            updatedData[blockNum].queue_length = updatedData[blockNum].queue.length;
          }
        }
        console.log(`Removed rejected truck ${rej.truck_id} from all queues`);
        return updatedData;
      });
    };

    websocketService.on('connect', connectHandler);
    websocketService.on('disconnect', disconnectHandler);
    websocketService.onGateIn(handleTruckArrivalCallback);
    websocketService.on('PREDICTION_RESULT', handlePredictionResultCallback);
    websocketService.on('PREDICTION_ERROR', errorHandler);
    websocketService.onPredictionRejected(rejectionHandler);

    return () => {
      console.log('Cleanup RealTimeQueue - removing event listeners');
      websocketService.off('connect', connectHandler);
      websocketService.off('disconnect', disconnectHandler);
      websocketService.off('GATE_IN', handleTruckArrivalCallback);
      websocketService.off('PREDICTION_RESULT', handlePredictionResultCallback);
      websocketService.off('PREDICTION_ERROR', errorHandler);
      websocketService.off('PREDICTION_REJECTED', rejectionHandler);
      // JANGAN set isConnected ke false saat cleanup - socket tetap terhubung
    };
  }, [handleConnectionStatus, handleTruckArrivalCallback, handlePredictionResultCallback]);

  // Update statistik ketika blok yang dipilih berubah
  useEffect(() => {
    if (selectedBlock && blocksData[selectedBlock]) {
      const block = blocksData[selectedBlock];
      setStatistics({
        trucks_in_queue: block.queue_length,
        avg_duration: block.queue_length > 0 
          ? block.total_duration / block.queue_length 
          : 0,
        total_time: block.total_duration,
        clear_time: block.total_duration
      });
    }
  }, [selectedBlock, blocksData]);

  // Fungsi pembantu
  const getBlockLabel = (blockNum) => {
    return blockNum === 7 ? 'D1' : `CY${blockNum}`;
  };

  const currentBlock = blocksData[selectedBlock] || {
    queue: [],
    queue_length: 0,
    total_duration: 0
  };

  // Sub-komponen
  const BlockButton = ({ blockNum }) => {
    const isSelected = selectedBlock === blockNum;
    const blockInfo = blocksData[blockNum];
    const queueCount = blockInfo?.queue_length || 0;
    const blockLabel = getBlockLabel(blockNum);

    return (
      <button
        onClick={() => setSelectedBlock(blockNum)}
        className={`relative p-3 rounded-lg transition-all duration-200 border-2 ${
          isSelected
            ? 'bg-blue-600 border-blue-600 shadow-lg transform scale-105'
            : 'bg-white border-gray-200 hover:border-blue-300 hover:shadow-md'
        }`}
      >
        <div className="flex flex-col items-center gap-1">
          <Layers className={`w-5 h-5 ${isSelected ? 'text-white' : 'text-gray-400'}`} />
          <div className={`text-sm font-bold ${isSelected ? 'text-white' : 'text-gray-700'}`}>
            {blockLabel}
          </div>
          {queueCount > 0 && (
            <div className={`absolute -top-2 -right-2 w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${
              isSelected ? 'bg-yellow-400 text-blue-900' : 'bg-blue-500 text-white'
            }`}>
              {queueCount}
            </div>
          )}
        </div>
      </button>
    );
  };

  const StatCard = ({ icon: Icon, label, value, color }) => (
    <div className="bg-white rounded-lg p-4 border-2 border-gray-100 hover:shadow-lg transition-all duration-200">
      <div className="flex items-center gap-3">
        <div className={`w-12 h-12 ${color} rounded-lg flex items-center justify-center shadow-md`}>
          <Icon className="w-6 h-6 text-white" />
        </div>
        <div className="flex-1">
          <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">{label}</p>
          <p className="text-xl font-bold text-gray-900">{value}</p>
        </div>
      </div>
    </div>
  );

  const TruckCard = ({ truck, index }) => {
    const parseLocation = (lokasi) => {
      const parts = lokasi.split(' ');
      return {
        slot: parts[0] || '0',
        row: parts[1] || '0',
        tier: parts[2] || '0'
      };
    };

    const formatTime = (timestamp) => {
      try {
        return new Date(timestamp).toLocaleString('id-ID', {
          year: 'numeric',
          month: '2-digit',
          day: '2-digit',
          hour: '2-digit',
          minute: '2-digit'
        });
      } catch {
        return timestamp;
      }
    };

    const location = parseLocation(truck.lokasi);
    const isPredicted = truck.status === 'predicted' && truck.predicted_duration;

    return (
      <div className="bg-white border-2 border-gray-200 rounded-lg p-2 hover:border-blue-300 hover:shadow-md transition-all duration-200 mb-1.5">
        <div className="flex items-start justify-between mb-1.5">
          <div className="flex items-center gap-1.5">
            <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center font-bold text-white text-xs">
              {index + 1}
            </div>
            <div>
              <h3 className="text-sm font-bold text-gray-900">{truck.truck_id}</h3>
              <p className="text-xs text-gray-600 font-medium">
                {truck.display_job_type || truck.job_type} • {truck.container_size}ft • {truck.ctr_status} • {truck.container_type}
              </p>
            </div>
          </div>
          {isConnected && (
            <span className={`px-2 py-0.5 rounded-full text-xs font-bold ${
              isPredicted ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'
            }`}>
              {isPredicted ? 'Ready' : 'Processing'}
            </span>
          )}
        </div>

        <div className="grid grid-cols-2 gap-1.5 mb-1.5">
          <div className="bg-blue-50 rounded-lg p-1.5 border border-blue-100">
            <div className="flex items-center gap-0.5 mb-0.5">
              <span className="w-1 h-1 bg-blue-600 rounded-full"></span>
              <span className="text-xs font-semibold text-blue-900 uppercase">Location</span>
            </div>
            <p className="text-xs font-bold text-blue-700">
              Slot {location.slot} • Row {location.row} • Tier {location.tier}
            </p>
          </div>
          <div className="bg-purple-50 rounded-lg p-1.5 border border-purple-100">
            <div className="flex items-center gap-0.5 mb-0.5">
              <span className="w-1 h-1 bg-purple-600 rounded-full"></span>
              <span className="text-xs font-semibold text-purple-900 uppercase">Stack</span>
            </div>
            <p className="text-xs font-bold text-purple-700">{truck.to_block}</p>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-1.5 pt-1.5 border-t border-gray-100">
          <div className="bg-green-50 rounded-lg p-1.5">
            <p className="text-xs font-semibold text-green-700 mb-0.5">Gate In</p>
            <p className="text-xs font-bold text-green-900">{formatTime(truck.gate_in_time)}</p>
          </div>
          {isPredicted ? (
            <div className="bg-blue-50 rounded-lg p-1.5">
              <p className="text-xs font-semibold text-blue-700 mb-0.5">Predicted Finish</p>
              <p className="text-xs font-bold text-blue-900">{formatTime(truck.expected_ready_time)}</p>
            </div>
          ) : (
            <div className="bg-gray-50 rounded-lg p-1.5 flex items-center justify-center">
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-gray-600"></div>
            </div>
          )}
        </div>

        {isPredicted && (
          <div className="mt-1.5 bg-gradient-to-r from-orange-50 to-orange-100 rounded-lg p-1.5 border border-orange-200">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-orange-700 uppercase">Duration</span>
              <span className="text-base font-bold text-orange-900">
                {truck.predicted_duration.toFixed(2)} min
              </span>
            </div>
          </div>
        )}
      </div>
    );
  };

  // Render utama
  return (
    <div className="flex-1 overflow-hidden px-6 py-4">
      <div className="max-w-full mx-auto space-y-4 h-full flex flex-col">
        
        {/* Connection Status Banner */}
        <div className={`flex items-center justify-between px-4 py-2 rounded-lg ${
          isConnected ? 'bg-green-50 border-2 border-green-200' : 'bg-red-50 border-2 border-red-200'
        }`}>
          <div className="flex items-center gap-3">
            <span className={`w-3 h-3 rounded-full ${isConnected ? 'bg-green-500 animate-pulse' : 'bg-red-500'}`}></span>
            <span className="text-sm font-bold text-gray-700">
              {isConnected ? 'Real-time Mode Active' : 'Disconnected'}
            </span>
            <span className="text-xs text-gray-500">•</span>
            <span className="text-xs text-gray-600">Auto-receiving trucks from WebSocket</span>
          </div>
          </div>

        {/* Block Selector */}
        <div className="grid grid-cols-7 gap-3 flex-shrink-0">
          {[1, 2, 3, 4, 5, 6, 7].map((num) => (
            <BlockButton key={num} blockNum={num} />
          ))}
        </div>

        {/* Statistics Cards */}
        <div className="grid grid-cols-4 gap-2 flex-shrink-0">
          <StatCard
            icon={Truck}
            label="Trucks in Queue"
            value={statistics.trucks_in_queue || 0}
            color="bg-blue-600"
          />
          <StatCard
            icon={Clock}
            label="Avg Duration"
            value={`${(statistics.avg_duration || 0).toFixed(2)} min`}
            color="bg-green-600"
          />
          <StatCard
            icon={TrendingUp}
            label="Total Time"
            value={`${(statistics.total_time || 0).toFixed(2)} min`}
            color="bg-orange-600"
          />
          <StatCard
            icon={AlertCircle}
            label="Clear Time"
            value={`${(statistics.clear_time || 0).toFixed(2)} min`}
            color="bg-purple-600"
          />
        </div>

        {/* Queue Display */}
        <div className="flex-1 min-h-0">
          <div className="bg-white rounded-xl shadow-md border-2 border-gray-200 h-full flex flex-col">
            <div className="bg-gradient-to-r from-blue-50 to-blue-100 px-5 py-4 border-b-2 border-blue-200 flex-shrink-0">
              <h2 className="text-xl font-bold text-gray-900 flex items-center gap-3">
                <Layers className="w-6 h-6 text-blue-600" />
                {getBlockLabel(selectedBlock)} - Real-time Queue
              </h2>
            </div>

            <div className="p-5 flex-1 min-h-0 overflow-y-auto custom-scrollbar">
              {currentBlock.queue_length === 0 ? (
                <div className="py-12 text-center">
                  <div className="w-20 h-20 bg-gray-100 rounded-full mx-auto mb-4 flex items-center justify-center">
                    <Truck className="w-10 h-10 text-gray-400" />
                  </div>
                  <h3 className="text-lg font-bold text-gray-700 mb-2">No Trucks in Queue</h3>
                  <p className="text-gray-500 text-sm">
                    {isConnected 
                      ? 'Waiting for trucks from WebSocket server...'
                      : 'Not connected to WebSocket server'}
                  </p>
                </div>
              ) : (
                <div className="space-y-3">
                  {currentBlock.queue.map((truck, index) => (
                    <TruckCard key={truck.truck_id} truck={truck} index={index} />
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      <style>{`
        .custom-scrollbar::-webkit-scrollbar {
          width: 8px;
        }
        .custom-scrollbar::-webkit-scrollbar-track {
          background: #f1f1f1;
          border-radius: 10px;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb {
          background: #cbd5e1;
          border-radius: 10px;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover {
          background: #94a3b8;
        }
        @keyframes spin {
          to { transform: rotate(360deg); }
        }
        .animate-spin {
          animation: spin 1s linear infinite;
        }
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.5; }
        }
        .animate-pulse {
          animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
        }
      `}</style>
    </div>
  );
}

export default RealTimeQueue;
