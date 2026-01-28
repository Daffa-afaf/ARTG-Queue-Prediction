import React, { useState, useEffect } from 'react';
import { Truck, Clock, TrendingUp, AlertCircle, Layers, Plus, X, Trash2 } from 'lucide-react';
import './App.css';
import RealTimeQueue from './components/RealTimeQueue';

function App() {
  const [mode, setMode] = useState('realtime');
  const [selectedBlock, setSelectedBlock] = useState(1);
  const [blocksData, setBlocksData] = useState({
    1: { queue: [], name: 'CY1' },
    2: { queue: [], name: 'CY2' },
    3: { queue: [], name: 'CY3' },
    4: { queue: [], name: 'CY4' },
    5: { queue: [], name: 'CY5' },
    6: { queue: [], name: 'CY6' },
    7: { queue: [], name: 'D1' }
  });
  const [showAddForm, setShowAddForm] = useState(false);
  const [formData, setFormData] = useState({
    truck_id: '',
    slot: '',
    row: '',
    tier: '',
    block: '',
    container_type: 'DRY',
    job_type: 'EXPORT',
    container_size: '40',
    ctr_status: 'FULL'
  });

  const currentBlock = blocksData[selectedBlock] || { queue: [], name: `Block ${selectedBlock}` };

  const calculateStatistics = () => {
    const currentQueue = blocksData[selectedBlock]?.queue || [];
    const totalTrucks = currentQueue.length;
    const trucksWithDuration = currentQueue.filter(t => t.predicted_duration);
    const totalDuration = trucksWithDuration.reduce((sum, t) => sum + (t.predicted_duration || 0), 0);
    const avgDuration = trucksWithDuration.length > 0 ? totalDuration / trucksWithDuration.length : 0;

    return {
      trucks_in_queue: totalTrucks,
      avg_duration: avgDuration || 0,
      total_time: totalDuration,
      clear_time: totalDuration
    };
  };

  const stats = calculateStatistics();

  const getBlockLabel = (num) => num === 7 ? 'D1' : `Block ${num}`;

  const handleLoadDemoData = async () => {
    try {
      const response = await fetch('http://localhost:5000/demo/populate', {
        method: 'POST'
      });

      if (!response.ok) {
        throw new Error('Failed to load demo data');
      }

      const data = await response.json();
      alert(`Demo data loaded! ${data.trucks_added} trucks added to queues`);

      // Reload data dari server
      await loadBlocksData();
    } catch (error) {
      console.error('Error loading demo data:', error);
      alert('Failed to load demo data. Make sure Flask backend is running.');
    }
  };

  const loadBlocksData = async () => {
    try {
      const response = await fetch('http://localhost:5000/blocks');
      const blocksData = await response.json();

      const updatedBlocks = {};
      for (let i = 1; i <= 7; i++) {
        if (blocksData[i]) {
          // Transform truck data ke format yang benar
          const transformedQueue = (blocksData[i].queue || []).map(truck => ({
            truck_id: truck.truck_id,
            lokasi: truck.lokasi,
            to_block: truck.block || truck.to_block || '-',
            container_size: truck.container_size || truck.size || '40',
            container_type: truck.container_type || truck.type || 'DRY',
            ctr_status: truck.ctr_status || truck.status || 'FULL',
            job_type: truck.job_type,
            display_job_type: truck.job_type === 'DELIVERY' ? 'DELIVERY' : 'RECEIVING',
            gate_in_time: truck.gate_in_time,
            predicted_duration: truck.predicted_duration || 0,
            status: truck.status || 'predicted'
          }));
          
          updatedBlocks[i] = {
            queue: transformedQueue,
            name: blocksData[i].name || `Block ${i}`
          };
        }
      }
      setBlocksData(updatedBlocks);
    } catch (error) {
      console.error('Error loading blocks data:', error);
    }
  };

  const handleAddTruck = async () => {
    if (!formData.slot || !formData.row || !formData.tier || !formData.block) {
      alert('Please fill all required fields');
      return;
    }

    const truckId = `T${Date.now().toString().slice(-6)}${Math.random().toString(36).substr(2, 3).toUpperCase()}`;

    try {
      const response = await fetch(`http://localhost:5000/blocks/${selectedBlock}/add_truck`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          truck_id: truckId,
          lokasi: `${formData.slot} ${formData.row} ${formData.tier}`,
          job_type: formData.job_type === 'EXPORT' ? 'DELIVERY' : 'RECEIVING',
          container_size: formData.container_size,
          container_type: formData.container_type,
          ctr_status: formData.ctr_status,
          block: formData.block
        })
      });

      if (!response.ok) {
        throw new Error('Failed to add truck');
      }

      const result = await response.json();
      const truck = result.truck;

      const newTruck = {
        truck_id: truck.truck_id,
        lokasi: truck.lokasi,
        to_block: formData.block,
        container_size: truck.container_size,
        container_type: truck.container_type,
        ctr_status: truck.ctr_status,
        job_type: truck.job_type,
        display_job_type: formData.job_type === 'EXPORT' ? 'DELIVERY' : 'RECEIVING',
        gate_in_time: truck.gate_in_time,
        predicted_duration: truck.predicted_duration || 0,
        status: truck.status || 'predicted'
      };

      setBlocksData(prev => ({
        ...prev,
        [selectedBlock]: {
          ...prev[selectedBlock],
          queue: [...prev[selectedBlock].queue, newTruck]
        }
      }));

      setShowAddForm(false);
      setFormData({
        truck_id: '',
        slot: '',
        row: '',
        tier: '',
        block: '',
        container_type: 'DRY',
        job_type: 'EXPORT',
        container_size: '40',
        ctr_status: 'FULL'
      });
    } catch (error) {
      console.error('Error:', error);
      alert('Failed to add truck');
    }
  };

  const handleRemoveTruck = (truckId) => {
    setBlocksData(prev => ({
      ...prev,
      [selectedBlock]: {
        ...prev[selectedBlock],
        queue: prev[selectedBlock].queue.filter(t => t.truck_id !== truckId)
      }
    }));
  };

  const handleClearBlock = () => {
    if (window.confirm(`Clear all trucks from ${getBlockLabel(selectedBlock)}?`)) {
      setBlocksData(prev => ({
        ...prev,
        [selectedBlock]: { ...prev[selectedBlock], queue: [] }
      }));
    }
  };

  const BlockButton = ({ blockNum }) => {
    const isSelected = selectedBlock === blockNum;
    const blockData = blocksData[blockNum];
    const queueLength = blockData?.queue?.length || 0;

    return (
      <button
        onClick={() => setSelectedBlock(blockNum)}
        className={`relative px-4 py-4 rounded-lg font-semibold transition-all duration-200 flex flex-col items-center justify-center gap-1 ${
          isSelected
            ? 'bg-blue-600 text-white shadow-lg scale-105'
            : 'bg-white text-gray-700 border-2 border-gray-200 hover:border-blue-300 hover:shadow-md'
        }`}
      >
        {queueLength > 0 && (
          <span className="absolute -top-2 -right-2 bg-yellow-500 text-white text-xs font-bold rounded-full w-5 h-5 flex items-center justify-center shadow-md">
            {queueLength}
          </span>
        )}
        <Layers className="w-4 h-4" />
        <span className="text-xs">{getBlockLabel(blockNum)}</span>
      </button>
    );
  };

  const StatCard = ({ icon: Icon, label, value, color }) => (
    <div className="bg-white rounded-lg p-3 border-2 border-gray-100 hover:shadow-lg transition-all duration-200">
      <div className="flex items-center gap-3">
        <div className={`w-11 h-11 ${color} rounded-lg flex items-center justify-center shadow-md flex-shrink-0`}>
          <Icon className="w-6 h-6 text-white" />
        </div>
        <div className="flex-1">
          <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-0.5">{label}</p>
          <p className="text-xl font-bold text-gray-900">{value}</p>
        </div>
      </div>
    </div>
  );

  const TruckCard = ({ truck, onRemove, queueIndex }) => {
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
    const isPredicted = truck.predicted_duration && truck.predicted_duration > 0;

    return (
      <div className="bg-white border-2 border-gray-300 rounded-lg p-2 hover:border-blue-400 hover:shadow-lg transition-all duration-200">
        {/* Header with Truck ID and Info */}
        <div className="flex items-start justify-between mb-2">
          <div className="flex items-start gap-2 flex-1">
            <div className="bg-blue-600 text-white font-bold rounded w-7 h-7 flex items-center justify-center text-xs flex-shrink-0">
              {queueIndex}
            </div>
            <div className="flex-1 min-w-0">
              <h3 className="text-sm font-bold text-gray-900">{truck.truck_id}</h3>
              <p className="text-xs text-gray-600 font-semibold">
                {truck.display_job_type} • {truck.container_size}ft • {truck.ctr_status}
              </p>
            </div>
          </div>
          <button
            onClick={() => onRemove(truck.truck_id)}
            className="text-red-500 hover:text-red-700 hover:bg-red-50 p-1 rounded flex-shrink-0 ml-1"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>

        {/* Location and Block */}
        <div className="grid grid-cols-2 gap-1.5 mb-2">
          <div className="bg-blue-50 rounded-lg p-1 border border-blue-300">
            <p className="text-xs font-bold text-blue-700 uppercase">Location</p>
            <p className="text-xs font-bold text-blue-900">
              {location.slot} • {location.row} • {location.tier}
            </p>
          </div>
          <div className="bg-purple-50 rounded-lg p-1 border border-purple-300">
            <p className="text-xs font-bold text-purple-700 uppercase">Block</p>
            <p className="text-xs font-bold text-purple-900">{truck.to_block || '-'}</p>
          </div>
        </div>

        {/* Gate In and Predicted Finish */}
        <div className="grid grid-cols-2 gap-1.5 mb-2">
          <div className="bg-green-50 rounded-lg p-1 border border-green-300">
            <p className="text-xs font-bold text-green-700 uppercase">Gate In</p>
            <p className="text-xs font-bold text-green-900">{formatTime(truck.gate_in_time)}</p>
          </div>
          {isPredicted && (
            <div className="bg-blue-50 rounded-lg p-1 border border-blue-300">
              <p className="text-xs font-bold text-blue-700 uppercase">Pred Finish</p>
              <p className="text-xs font-bold text-blue-900">
                {formatTime(new Date(new Date(truck.gate_in_time).getTime() + truck.predicted_duration * 60000).toISOString())}
              </p>
            </div>
          )}
        </div>

        {/* Duration */}
        {isPredicted && (
          <div className="bg-orange-100 rounded-lg p-1.5 border border-orange-400">
            <div className="flex items-center justify-between">
              <p className="text-xs font-bold text-orange-700 uppercase">Duration</p>
              <p className="text-base font-bold text-orange-900">
                {truck.predicted_duration.toFixed(2)} min
              </p>
            </div>
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="h-screen bg-gray-50 flex flex-col overflow-hidden">
      {/* Header */}
      <header className="bg-blue-600 text-white shadow-lg flex-shrink-0">
        <div className="px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="bg-white rounded-lg p-2">
                <img 
                  src="/logo.png" 
                  alt="logo" 
                  className="h-8 w-8 object-contain"
                  onError={(e) => {
                    e.target.style.display = 'none';
                  }}
                />
              </div>
              <div>
                <h1 className="text-2xl font-bold">PELINDO - ARTG Terminal</h1>
                <p className="text-blue-100 text-sm">Multi-Block Queue Management System</p>
              </div>
            </div>
            <button 
              onClick={handleLoadDemoData}
              className="bg-purple-600 hover:bg-purple-700 text-white font-semibold py-1.5 px-4 rounded-lg shadow-md transition duration-200 text-sm"
            >
              Load Demo Data
            </button>
          </div>
        </div>
      </header>

      {/* Operating Mode Selector */}
      <div className="px-6 py-2 flex-shrink-0">
        <div className="bg-white rounded-lg shadow-md p-3">
          <h2 className="text-sm font-semibold text-gray-700 mb-2">Operating Mode:</h2>
          <div className="flex space-x-3">
            <button
              onClick={() => setMode('batch')}
              className={`flex-1 py-2 px-4 rounded-lg font-semibold transition duration-200 text-sm ${
                mode === 'batch'
                  ? 'bg-gray-400 text-white shadow-lg'
                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
              }`}
            >
              Batch Mode (Manual Input)
            </button>
            <button
              onClick={() => setMode('realtime')}
              className={`flex-1 py-2 px-4 rounded-lg font-semibold transition duration-200 text-sm ${
                mode === 'realtime'
                  ? 'bg-green-600 text-white shadow-lg'
                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
              }`}
            >
              Real-time Mode (Live Queue)
            </button>
          </div>
        </div>
      </div>

      {mode === 'batch' ? (
        <>
        {/* Batch Mode Content */}
        <div className="flex-1 overflow-hidden px-6 py-4">
          <div className="max-w-full mx-auto space-y-4 h-full flex flex-col">
            
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
                value={stats.trucks_in_queue || 0}
                color="bg-blue-600"
              />
              <StatCard
                icon={Clock}
                label="Avg Duration"
                value={`${stats.avg_duration.toFixed(2)} min`}
                color="bg-green-600"
              />
              <StatCard
                icon={TrendingUp}
                label="Total Time"
                value={`${stats.total_time.toFixed(2)} min`}
                color="bg-orange-600"
              />
              <StatCard
                icon={AlertCircle}
                label="Clear Time"
                value={`${stats.clear_time.toFixed(2)} min`}
                color="bg-purple-600"
              />
            </div>

            {/* Queue Display with Add Truck Panel */}
            <div className="flex-1 min-h-0 grid grid-cols-3 gap-4">
              {/* Queue List */}
              <div className="col-span-2 bg-white rounded-xl shadow-md border-2 border-gray-200 flex flex-col overflow-hidden">
                <div className="bg-gradient-to-r from-blue-50 to-blue-100 px-5 py-4 border-b-2 border-blue-200 flex items-center justify-between flex-shrink-0">
                  <h2 className="text-xl font-bold text-gray-900 flex items-center gap-3">
                    <Layers className="w-6 h-6 text-blue-600" />
                    {getBlockLabel(selectedBlock)} - Queue
                  </h2>
                  {currentBlock.queue.length > 0 && (
                    <button
                      onClick={handleClearBlock}
                      className="bg-red-600 hover:bg-red-700 text-white px-3 py-1.5 rounded-lg font-semibold flex items-center gap-2 transition text-sm"
                    >
                      <Trash2 className="w-4 h-4" />
                      Clear Block
                    </button>
                  )}
                </div>

              {currentBlock.queue.length > 0 && (
                <div className="px-5 py-3 bg-blue-50 border-b border-blue-200 flex items-center justify-between flex-shrink-0">
                  <span className="text-sm font-semibold text-gray-700">
                    {currentBlock.queue.length} truck{currentBlock.queue.length > 1 ? 's' : ''} in queue
                  </span>
                  <span className="text-sm font-bold text-blue-900">
                    Total: {currentBlock.queue.reduce((sum, t) => sum + (t.predicted_duration || 0), 0).toFixed(2)} min
                  </span>
                </div>
              )}

              <div className="flex-1 min-h-0 overflow-y-auto custom-scrollbar p-5">
                {currentBlock.queue.length === 0 ? (
                  <div className="py-12 text-center">
                    <div className="w-20 h-20 bg-gray-100 rounded-full mx-auto mb-4 flex items-center justify-center">
                      <Truck className="w-10 h-10 text-gray-400" />
                    </div>
                    <h3 className="text-lg font-bold text-gray-700 mb-2">No Trucks in Queue</h3>
                    <p className="text-gray-500 text-sm">
                      Add trucks using the form on the right
                    </p>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {currentBlock.queue.map((truck, index) => (
                      <TruckCard key={truck.truck_id} truck={truck} onRemove={handleRemoveTruck} queueIndex={index + 1} />
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* Add Truck Form Panel */}
            <div className="bg-white rounded-xl shadow-md border-2 border-gray-200 flex flex-col overflow-hidden">
              <div className="bg-gradient-to-r from-green-50 to-green-100 px-4 py-3 border-b-2 border-green-200 flex-shrink-0">
                <div className="flex items-center gap-3">
                  <div className="w-9 h-9 bg-blue-600 rounded-lg flex items-center justify-center flex-shrink-0">
                    <Plus className="w-5 h-5 text-white" />
                  </div>
                  <h2 className="text-base font-bold text-gray-900">Add Truck to Queue</h2>
                </div>
              </div>

              {!showAddForm ? (
                <div className="p-6 flex items-center justify-center flex-1">
                  <button
                    onClick={() => setShowAddForm(true)}
                    className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-6 rounded-lg shadow-lg hover:shadow-xl transition-all duration-200 flex items-center justify-center gap-2"
                  >
                    <Plus className="w-5 h-5" />
                    Open Form
                  </button>
                </div>
              ) : (
                <div className="flex-1 min-h-0 overflow-y-auto custom-scrollbar p-4">
                  <div className="space-y-3">
                    <div className="grid grid-cols-3 gap-2">
                      <div>
                        <label className="block text-xs font-bold text-gray-700 mb-1">SLOT</label>
                        <input
                          type="text"
                          value={formData.slot}
                          onChange={(e) => setFormData({...formData, slot: e.target.value})}
                          className="w-full px-3 py-2 border-2 border-gray-300 rounded-lg focus:border-blue-500 focus:outline-none text-center"
                          placeholder="42"
                        />
                      </div>
                      <div>
                        <label className="block text-xs font-bold text-gray-700 mb-1">ROW</label>
                        <input
                          type="text"
                          value={formData.row}
                          onChange={(e) => setFormData({...formData, row: e.target.value})}
                          className="w-full px-3 py-2 border-2 border-gray-300 rounded-lg focus:border-blue-500 focus:outline-none text-center"
                          placeholder="06"
                        />
                      </div>
                      <div>
                        <label className="block text-xs font-bold text-gray-700 mb-1">TIER</label>
                        <input
                          type="text"
                          value={formData.tier}
                          onChange={(e) => setFormData({...formData, tier: e.target.value})}
                          className="w-full px-3 py-2 border-2 border-gray-300 rounded-lg focus:border-blue-500 focus:outline-none text-center"
                          placeholder="1"
                        />
                      </div>
                    </div>

                    <div>
                      <label className="block text-xs font-bold text-gray-700 mb-1">BLOCK (Destination)</label>
                      <input
                        type="text"
                        value={formData.block}
                        onChange={(e) => setFormData({...formData, block: e.target.value})}
                        className="w-full px-3 py-2 border-2 border-gray-300 rounded-lg focus:border-blue-500 focus:outline-none"
                        placeholder="e.g., 1A, 1G, 2C, D1"
                      />
                    </div>

                    <div>
                      <label className="block text-xs font-bold text-gray-700 mb-1">CONTAINER TYPE</label>
                      <select
                        value={formData.container_type}
                        onChange={(e) => setFormData({...formData, container_type: e.target.value})}
                        className="w-full px-3 py-2 border-2 border-gray-300 rounded-lg focus:border-blue-500 focus:outline-none"
                      >
                        <option value="DRY">DRY</option>
                        <option value="TANK">TANK</option>
                        <option value="REEFER">REEFER</option>
                        <option value="OVD">OVERDRIVE</option>
                        <option value="O/T">O/T</option>
                        <option value="FLT">FLT</option>
                      </select>
                    </div>

                    <div>
                      <label className="block text-xs font-bold text-gray-700 mb-1">JOB TYPE</label>
                      <select
                        value={formData.job_type}
                        onChange={(e) => setFormData({...formData, job_type: e.target.value})}
                        className="w-full px-3 py-2 border-2 border-gray-300 rounded-lg focus:border-blue-500 focus:outline-none"
                      >
                        <option value="EXPORT">Delivery</option>
                        <option value="IMPORT">Receiving</option>
                      </select>
                    </div>

                    <div className="grid grid-cols-2 gap-2">
                      <div>
                        <label className="block text-xs font-bold text-gray-700 mb-1">SIZE</label>
                        <select
                          value={formData.container_size}
                          onChange={(e) => setFormData({...formData, container_size: e.target.value})}
                          className="w-full px-3 py-2 border-2 border-gray-300 rounded-lg focus:border-blue-500 focus:outline-none"
                        >
                          <option value="20">20ft</option>
                          <option value="40">40ft</option>
                          <option value="45">45ft</option>
                        </select>
                      </div>
                      <div>
                        <label className="block text-xs font-bold text-gray-700 mb-1">STATUS</label>
                        <select
                          value={formData.ctr_status}
                          onChange={(e) => setFormData({...formData, ctr_status: e.target.value})}
                          className="w-full px-3 py-2 border-2 border-gray-300 rounded-lg focus:border-blue-500 focus:outline-none"
                        >
                          <option value="FULL">Full</option>
                          <option value="MTY">Empty</option>
                        </select>
                      </div>
                    </div>

                    <div className="flex gap-2 pt-2">
                      <button
                        onClick={handleAddTruck}
                        className="flex-1 bg-green-600 hover:bg-green-700 text-white font-bold py-2 px-4 rounded-lg transition"
                      >
                        Add Truck
                      </button>
                      <button
                        onClick={() => setShowAddForm(false)}
                        className="bg-gray-400 hover:bg-gray-500 text-white font-bold py-2 px-4 rounded-lg transition"
                      >
                        <X className="w-5 h-5" />
                      </button>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Footer */}
      <footer className="text-center py-3 text-gray-600 text-sm flex-shrink-0 border-t">
        © 2025 Pelindo Regional III - ARTG Terminal
      </footer>

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
      `}</style>
      </>
      ) : (
        /* Real-time Mode Content */
        <RealTimeQueue />
      )}
    </div>
  );
}

export default App;
