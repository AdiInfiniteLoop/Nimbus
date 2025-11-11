'use client'
import React, { useState, useEffect } from 'react';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { Server, Box, Activity, Cpu, TrendingUp, Search, Filter, Plus, Trash2, AlertCircle, CheckCircle, Clock } from 'lucide-react';

const API_BASE = 'http://localhost:5001';

const Dashboard = () => {
  const [clusterData, setClusterData] = useState(null);
  const [predictions, setPredictions] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [sortBy, setSortBy] = useState('cpu');
  const [selectedNode, setSelectedNode] = useState(null);
  const [loading, setLoading] = useState(true);
  const [cpuHistory, setCpuHistory] = useState({});
  
  // Form states
  const [showNodeForm, setShowNodeForm] = useState(false);
  const [showPodForm, setShowPodForm] = useState(false);
  const [nodeCpu, setNodeCpu] = useState(4);
  const [podCpu, setPodCpu] = useState(1);
  const [podImage, setPodImage] = useState('nginx:latest');

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 5000);
    return () => clearInterval(interval);
  }, []);

  const fetchData = async () => {
    try {
      const [clusterRes, predRes] = await Promise.all([
        fetch(`${API_BASE}/cluster/status`),
        fetch(`${API_BASE}/cluster/predictions`).catch(() => null)
      ]);
      
      const cluster = await clusterRes.json();
      setClusterData(cluster);
      
      if (predRes && predRes.ok) {
        const pred = await predRes.json();
        setPredictions(pred);
      }
      
      // Update CPU history for charts
      setCpuHistory(prev => {
        const newHistory = { ...prev };
        Object.entries(cluster.nodes).forEach(([nodeId, node]) => {
          if (!newHistory[nodeId]) newHistory[nodeId] = [];
          const oldArray = newHistory[nodeId] ? [...newHistory[nodeId]] : [];
          const cpuUsed = node.cpu_capacity - node.cpu_available;
          const cpuPercent = (cpuUsed / node.cpu_capacity) * 100;
          oldArray.push({
            time: new Date().toLocaleTimeString(),
            usage: cpuPercent,
            timestamp: Date.now()
          });
          // Keep last 20 points
          if (oldArray.length > 20) oldArray.shift();
          newHistory[nodeId] = oldArray
        });
        return newHistory;
      });
      
      setLoading(false);
    } catch (error) {
      console.error('Error fetching data:', error);
      setLoading(false);
    }
  };

  const addNode = async () => {
    try {
      const res = await fetch(`${API_BASE}/nodes`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ cpu_capacity: nodeCpu })
      });
      if (res.ok) {
        fetchData();
        setShowNodeForm(false);
        setNodeCpu(4);
      }
    } catch (error) {
      console.error('Error adding node:', error);
    }
  };

  const removeNode = async (nodeId) => {
    if (!confirm('Remove this node? Pods will be rescheduled.')) return;
    try {
      await fetch(`${API_BASE}/nodes/${nodeId}`, { method: 'DELETE' });
      fetchData();
    } catch (error) {
      console.error('Error removing node:', error);
    }
  };

  const createPod = async () => {
    try {
      const res = await fetch(`${API_BASE}/pods`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ cpu_required: podCpu, image: podImage })
      });
      if (res.ok) {
        fetchData();
        setShowPodForm(false);
        setPodCpu(1);
        setPodImage('nginx:latest');
      }
    } catch (error) {
      console.error('Error creating pod:', error);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen bg-slate-900">
        <div className="text-white text-xl">Loading cluster data...</div>
      </div>
    );
  }

  const nodes = clusterData?.nodes || {};
  const nodeArray = Object.entries(nodes).map(([id, data]) => ({ id, ...data }));

  // Filtering and sorting
  const filteredNodes = nodeArray
    .filter(node => {
      const matchesSearch = node.id.toLowerCase().includes(searchTerm.toLowerCase());
      const matchesStatus = statusFilter === 'all' || node.status === statusFilter;
      return matchesSearch && matchesStatus;
    })
    .sort((a, b) => {
      if (sortBy === 'cpu') return b.cpu_capacity - a.cpu_capacity;
      if (sortBy === 'available') return b.cpu_available - a.cpu_available;
      if (sortBy === 'pods') return b.pods.length - a.pods.length;
      return 0;
    });

  // Calculate cluster metrics
  const totalCpu = nodeArray.reduce((sum, n) => sum + n.cpu_capacity, 0);
  const usedCpu = nodeArray.reduce((sum, n) => sum + (n.cpu_capacity - n.cpu_available), 0);
  const totalPods = nodeArray.reduce((sum, n) => sum + n.pods.length, 0);
  const healthyNodes = nodeArray.filter(n => n.status === 'healthy').length;

  const COLORS = ['#10b981', '#3b82f6', '#f59e0b', '#ef4444', '#8b5cf6'];

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 text-white p-6">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-4xl font-bold mb-2 bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent">
          Cluster Orchestrator
        </h1>
        <p className="text-slate-400">Real-time monitoring and management dashboard</p>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
        <div className="bg-slate-800 rounded-lg p-6 border border-slate-700 hover:border-blue-500 transition-all">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-slate-400 text-sm">Total Nodes</p>
              <p className="text-3xl font-bold mt-1">{nodeArray.length}</p>
              <p className="text-green-400 text-sm mt-1">{healthyNodes} healthy</p>
            </div>
            <Server className="text-blue-400" size={40} />
          </div>
        </div>

        <div className="bg-slate-800 rounded-lg p-6 border border-slate-700 hover:border-green-500 transition-all">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-slate-400 text-sm">Total Pods</p>
              <p className="text-3xl font-bold mt-1">{totalPods}</p>
              <p className="text-slate-400 text-sm mt-1">Running</p>
            </div>
            <Box className="text-green-400" size={40} />
          </div>
        </div>

        <div className="bg-slate-800 rounded-lg p-6 border border-slate-700 hover:border-purple-500 transition-all">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-slate-400 text-sm">CPU Usage</p>
              <p className="text-3xl font-bold mt-1">{((usedCpu / totalCpu) * 100).toFixed(1)}%</p>
              <p className="text-slate-400 text-sm mt-1">{usedCpu} / {totalCpu} cores</p>
            </div>
            <Cpu className="text-purple-400" size={40} />
          </div>
        </div>

        <div className="bg-slate-800 rounded-lg p-6 border border-slate-700 hover:border-yellow-500 transition-all">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-slate-400 text-sm">Avg Load</p>
              <p className="text-3xl font-bold mt-1">
                {nodeArray.length > 0 ? ((usedCpu / totalCpu) * 100).toFixed(0) : 0}%
              </p>
              <p className="text-slate-400 text-sm mt-1">Per node</p>
            </div>
            <Activity className="text-yellow-400" size={40} />
          </div>
        </div>
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
        {/* CPU Distribution */}
        <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
          <h3 className="text-xl font-semibold mb-4 flex items-center gap-2">
            <Activity className="text-blue-400" size={20} />
            CPU Distribution
          </h3>
          <ResponsiveContainer width="100%" height={250}>
            <PieChart>
              <Pie
                data={nodeArray.map(n => ({
                  name: `Node ${n.id.slice(0, 8)}`,
                  value: n.cpu_capacity - n.cpu_available
                }))}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={(entry) => `${entry.value} cores`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {nodeArray.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Real-time CPU Usage */}
        <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
          <h3 className="text-xl font-semibold mb-4 flex items-center gap-2">
            <TrendingUp className="text-green-400" size={20} />
            Real-time CPU Usage
          </h3>
          <ResponsiveContainer width="100%" height={250}>
            <LineChart data={cpuHistory[Object.keys(cpuHistory)[0]] || []}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis dataKey="time" stroke="#9ca3af" />
              <YAxis stroke="#9ca3af" />
              <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #475569' }} />
              <Legend />
              {Object.entries(cpuHistory).map(([nodeId, history], idx) => (
                <Line
                  key={nodeId}
                  type="monotone"
                  dataKey="usage"
                  data={history}
                  stroke={COLORS[idx % COLORS.length]}
                  strokeWidth={2}
                  dot={false}
                  name={`Node ${nodeId.slice(0, 8)}`}
                />
              ))}
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Controls */}
      <div className="flex flex-wrap gap-4 mb-6">
        <div className="flex-1 min-w-[200px]">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400" size={20} />
            <input
              type="text"
              placeholder="Search nodes..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 bg-slate-800 border border-slate-700 rounded-lg focus:outline-none focus:border-blue-500"
            />
          </div>
        </div>

        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg focus:outline-none focus:border-blue-500"
        >
          <option value="all">All Status</option>
          <option value="healthy">Healthy</option>
          <option value="unhealthy">Unhealthy</option>
        </select>

        <select
          value={sortBy}
          onChange={(e) => setSortBy(e.target.value)}
          className="px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg focus:outline-none focus:border-blue-500"
        >
          <option value="cpu">Sort by CPU</option>
          <option value="available">Sort by Available</option>
          <option value="pods">Sort by Pods</option>
        </select>

        <button
          onClick={() => setShowNodeForm(true)}
          className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg flex items-center gap-2 transition-colors"
        >
          <Plus size={20} /> Add Node
        </button>

        <button
          onClick={() => setShowPodForm(true)}
          className="px-4 py-2 bg-green-600 hover:bg-green-700 rounded-lg flex items-center gap-2 transition-colors"
        >
          <Plus size={20} /> Create Pod
        </button>
      </div>

      {/* Nodes Table */}
      <div className="bg-slate-800 rounded-lg border border-slate-700 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-slate-700">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-slate-300 uppercase tracking-wider">
                  Node ID
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-slate-300 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-slate-300 uppercase tracking-wider">
                  CPU
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-slate-300 uppercase tracking-wider">
                  Pods
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-slate-300 uppercase tracking-wider">
                  Prediction
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-slate-300 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-700">
              {filteredNodes.map((node) => {
                const cpuUsage = ((node.cpu_capacity - node.cpu_available) / node.cpu_capacity) * 100;
                const prediction = predictions?.predictions?.[node.id];
                
                return (
                  <tr key={node.id} className="hover:bg-slate-700 transition-colors cursor-pointer" onClick={() => setSelectedNode(node)}>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center gap-2">
                        <Server size={16} className="text-blue-400" />
                        <span className="font-mono text-sm">{node.id.slice(0, 12)}...</span>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 py-1 rounded-full text-xs flex items-center gap-1 w-fit ${
                        node.status === 'healthy' 
                          ? 'bg-green-900 text-green-300' 
                          : 'bg-red-900 text-red-300'
                      }`}>
                        {node.status === 'healthy' ? <CheckCircle size={12} /> : <AlertCircle size={12} />}
                        {node.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          <div className="flex-1 h-2 bg-slate-600 rounded-full overflow-hidden">
                            <div 
                              className={`h-full transition-all ${
                                cpuUsage > 80 ? 'bg-red-500' : cpuUsage > 60 ? 'bg-yellow-500' : 'bg-green-500'
                              }`}
                              style={{ width: `${cpuUsage}%` }}
                            />
                          </div>
                          <span className="text-sm">{cpuUsage.toFixed(0)}%</span>
                        </div>
                        <div className="text-xs text-slate-400">
                          {node.cpu_capacity - node.cpu_available} / {node.cpu_capacity} cores
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="px-2 py-1 bg-slate-700 rounded text-sm">
                        {node.pods.length} pods
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {prediction ? (
                        <div className="flex items-center gap-2">
                          <TrendingUp size={14} className="text-purple-400" />
                          <span className="text-sm">{prediction.predicted_cpu.toFixed(1)}%</span>
                        </div>
                      ) : (
                        <span className="text-xs text-slate-500">Training...</span>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          removeNode(node.id);
                        }}
                        className="p-2 text-red-400 hover:bg-red-900 rounded transition-colors"
                      >
                        <Trash2 size={16} />
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Node Details Modal */}
      {selectedNode && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50" onClick={() => setSelectedNode(null)}>
          <div className="bg-slate-800 rounded-lg p-6 max-w-2xl w-full border border-slate-700" onClick={(e) => e.stopPropagation()}>
            <h3 className="text-2xl font-bold mb-4">Node Details</h3>
            <div className="space-y-4">
              <div>
                <p className="text-slate-400 text-sm">Node ID</p>
                <p className="font-mono">{selectedNode.id}</p>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-slate-400 text-sm">CPU Capacity</p>
                  <p className="text-xl">{selectedNode.cpu_capacity} cores</p>
                </div>
                <div>
                  <p className="text-slate-400 text-sm">Available</p>
                  <p className="text-xl">{selectedNode.cpu_available} cores</p>
                </div>
              </div>
              <div>
                <p className="text-slate-400 text-sm mb-2">Running Pods ({selectedNode.pods.length})</p>
                <div className="space-y-2 max-h-48 overflow-y-auto">
                  {selectedNode.pods.map((pod, idx) => (
                    <div key={idx} className="bg-slate-700 p-3 rounded flex items-center gap-2">
                      <Box size={16} className="text-green-400" />
                      <span className="font-mono text-sm">{pod.id?.slice(0, 12) || pod}</span>
                    </div>
                  ))}
                </div>
              </div>
              <button
                onClick={() => setSelectedNode(null)}
                className="w-full py-2 bg-slate-700 hover:bg-slate-600 rounded transition-colors"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Add Node Modal */}
      {showNodeForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50" onClick={() => setShowNodeForm(false)}>
          <div className="bg-slate-800 rounded-lg p-6 max-w-md w-full border border-slate-700" onClick={(e) => e.stopPropagation()}>
            <h3 className="text-2xl font-bold mb-4">Add New Node</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm text-slate-400 mb-2">CPU Capacity (cores)</label>
                <input
                  type="number"
                  min="1"
                  max="8"
                  value={nodeCpu}
                  onChange={(e) => {
                  const valnode = e.target.value
                  setNodeCpu(valnode == '' ? '' : valnode)}}
                  className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded focus:outline-none focus:border-blue-500"
                />
              </div>
              <div className="flex gap-2">
                <button
                  onClick={addNode}
                  className="flex-1 py-2 bg-blue-600 hover:bg-blue-700 rounded transition-colors"
                >
                  Create Node
                </button>
                <button
                  onClick={() => setShowNodeForm(false)}
                  className="flex-1 py-2 bg-slate-700 hover:bg-slate-600 rounded transition-colors"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Create Pod Modal */}
      {showPodForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50" onClick={() => setShowPodForm(false)}>
          <div className="bg-slate-800 rounded-lg p-6 max-w-md w-full border border-slate-700" onClick={(e) => e.stopPropagation()}>
            <h3 className="text-2xl font-bold mb-4">Create New Pod</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm text-slate-400 mb-2">CPU Required (cores)</label>
                <input
                  type="number"
                  min="1"
                  max="6"
                  value={podCpu}
                  onChange={(e) => {
                    const val = e.target.value
                    setPodCpu(val == '' ? '' : parseInt(val))
                    }}
                  className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded focus:outline-none focus:border-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm text-slate-400 mb-2">Container Image</label>
                <input
                  type="text"
                  value={podImage}
                  onChange={(e) => setPodImage(e.target.value)}
                  className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded focus:outline-none focus:border-blue-500"
                  placeholder="nginx:latest"
                />
              </div>
              <div className="flex gap-2">
                <button
                  onClick={createPod}
                  className="flex-1 py-2 bg-green-600 hover:bg-green-700 rounded transition-colors"
                >
                  Create Pod
                </button>
                <button
                  onClick={() => setShowPodForm(false)}
                  className="flex-1 py-2 bg-slate-700 hover:bg-slate-600 rounded transition-colors"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Dashboard;
