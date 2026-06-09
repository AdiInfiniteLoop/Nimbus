'use client'
import React, { useState, useEffect } from 'react';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { Server, Box, Activity, Cpu, TrendingUp, Search, Plus, Trash2, AlertCircle, CheckCircle, Loader, RefreshCw, Download, Upload, Mail, Settings, Zap, Moon, Sun, Bell, FileText, Play, Pause } from 'lucide-react';
import Link from 'next/link'
const API_BASE = 'http://localhost:5001';

const LoadingSpinner = ({ size = 'md', text = '' }) => {
  const sizes = { sm: 'w-4 h-4', md: 'w-8 h-8', lg: 'w-12 h-12' };
  return (
    <div className="flex flex-col items-center justify-center gap-2">
      <Loader className={`${sizes[size]} animate-spin text-blue-400`} />
      {text && <p className="text-slate-400 text-sm">{text}</p>}
    </div>
  );
};

const Dashboard = () => {
  const [clusterData, setClusterData] = useState(null);
  const [predictions, setPredictions] = useState(null);
  const [autoscalerStatus, setAutoscalerStatus] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [sortBy, setSortBy] = useState('cpu');
  const [selectedNode, setSelectedNode] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [cpuHistory, setCpuHistory] = useState({});
  const [actionLoading, setActionLoading] = useState(null);
  const [theme, setTheme] = useState('dark');
  
  // Modal states
  const [showNodeForm, setShowNodeForm] = useState(false);
  const [showPodForm, setShowPodForm] = useState(false);
  const [showSettingsModal, setShowSettingsModal] = useState(false);
  const [showAlertConfig, setShowAlertConfig] = useState(false);
  
  // Form states
  const [nodeCpu, setNodeCpu] = useState(4);
  const [podCpu, setPodCpu] = useState(1);
  const [podImage, setPodImage] = useState('nginx:latest');

  const [allowed, setAllowed] = useState(false);

useEffect(() => {
  try {
    const raw = localStorage.getItem("session");
    if (!raw) {
      setAllowed(false);
      setLoading(false);
      return;
    }

    const data = JSON.parse(raw);

    // Validate structure AND username
    if (data?.username === "admin") {
      setAllowed(true);
    } else {
      setAllowed(false);
    }
  } catch (err) {
    console.error("Session parse error", err);
    setAllowed(false);
  }

  setLoading(false);
}, []);
  
  // Settings states
  const [autoscalerConfig, setAutoscalerConfig] = useState({
    scale_up_threshold: 75,
    scale_down_threshold: 30,
    min_nodes: 1,
    max_nodes: 10,
    scale_up_cpu: 4,
    cooldown_seconds: 60
  });
  
  const [alertConfig, setAlertConfig] = useState({
    enabled: false,
    recipient_emails: ''
  });

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 5000);
    return () => clearInterval(interval);
  }, []);

  const fetchData = async (showLoader = false) => {
    if (showLoader) setRefreshing(true);
    
    try {
      const [clusterRes, predRes, autoRes] = await Promise.all([
        fetch(`${API_BASE}/cluster/status`),
        fetch(`${API_BASE}/cluster/predictions`).catch(() => null),
        fetch(`${API_BASE}/autoscaler/status`).catch(() => null)
      ]);
      
      const cluster = await clusterRes.json();
      setClusterData(cluster);
      
      if (predRes && predRes.ok) {
        const pred = await predRes.json();
        setPredictions(pred);
      }
      
      if (autoRes && autoRes.ok) {
        const auto = await autoRes.json();
        setAutoscalerStatus(auto);
      }
      
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
          if (oldArray.length > 20) oldArray.shift();
          newHistory[nodeId] = oldArray;   });
        return newHistory;
      });
      
      setLoading(false);
      setRefreshing(false);
    } catch (error) {
      console.error('Error fetching data:', error);
      setLoading(false);
      setRefreshing(false);
    }
  };

  const toggleAutoscaler = async () => {
    setActionLoading('autoscaler-toggle');
    const endpoint = autoscalerStatus?.enabled ? 'disable' : 'enable';
    try {
      await fetch(`${API_BASE}/autoscaler/${endpoint}`, { method: 'POST' });
      await fetchData();
    } catch (error) {
      console.error('Error toggling autoscaler:', error);
    } finally {
      setActionLoading(null);
    }
  };

  const updateAutoscalerConfig = async () => {
    setActionLoading('update-config');
    try {
      await fetch(`${API_BASE}/autoscaler/config`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(autoscalerConfig)
      });
      alert('Configuration updated successfully');
      setShowSettingsModal(false);
    } catch (error) {
      alert('Failed to update configuration');
    } finally {
      setActionLoading(null);
    }
  };

  const exportLogs = async (format) => {
    setActionLoading(`export-${format}`);
    try {
      const res = await fetch(`${API_BASE}/logs/export?format=${format}`);
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `logs_${new Date().toISOString().slice(0,10)}.${format}`;
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      alert('Failed to export logs');
    } finally {
      setActionLoading(null);
    }
  };

  const saveClusterConfig = async () => {
    setActionLoading('save-config');
    try {
      await fetch(`${API_BASE}/cluster/config/save`, { method: 'POST' });
      alert('Cluster configuration saved successfully');
    } catch (error) {
      alert('Failed to save configuration');
    } finally {
      setActionLoading(null);
    }
  };

  const exportClusterConfig = async () => {
    setActionLoading('export-config');
    try {
      const res = await fetch(`${API_BASE}/cluster/config/export`);
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `cluster_config_${new Date().toISOString().slice(0,10)}.json`;
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      alert('Failed to export configuration');
    } finally {
      setActionLoading(null);
    }
  };

  const toggleAlerts = async () => {
    const endpoint = alertConfig.enabled ? 'disable' : 'enable';
    try {
      await fetch(`${API_BASE}/alerts/${endpoint}`, { method: 'POST' });
      setAlertConfig(prev => ({ ...prev, enabled: !prev.enabled }));
    } catch (error) {
      alert('Failed to toggle alerts');
    }
  };

  const sendTestAlert = async () => {
    setActionLoading('test-alert');
    try {
      await fetch(`${API_BASE}/alerts/test`, { method: 'POST' });
      alert('Test alert sent! Check console logs.');
    } catch (error) {
      alert('Failed to send test alert');
    } finally {
      setActionLoading(null);
    }
  };

  const addNode = async () => {
    setActionLoading('add-node');
    try {
      const res = await fetch(`${API_BASE}/nodes`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ cpu_capacity: nodeCpu })
      });
      if (res.ok) {
        await fetchData();
        setShowNodeForm(false);
        setNodeCpu(4);
      } else {
        const error = await res.json();
        alert(`Error: ${error.error}`);
      }
    } catch (error) {
      alert('Failed to add node');
    } finally {
      setActionLoading(null);
    }
  };

  const removeNode = async (nodeId) => {
    if (!confirm('Remove this node? Pods will be rescheduled.')) return;
    setActionLoading(`remove-${nodeId}`);
    try {
      await fetch(`${API_BASE}/nodes/${nodeId}`, { method: 'DELETE' });
      await fetchData();
    } catch (error) {
      alert('Failed to remove node');
    } finally {
      setActionLoading(null);
    }
  };

  const createPod = async () => {
    setActionLoading('create-pod');
    try {
      const res = await fetch(`${API_BASE}/pods`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ cpu_required: podCpu, image: podImage })
      });
      if (res.ok) {
        await fetchData();
        setShowPodForm(false);
        setPodCpu(1);
        setPodImage('nginx:latest');
      } else {
        const error = await res.json();
        alert(`Error: ${error.error}`);
      }
    } catch (error) {
      alert('Failed to create pod');
    } finally {
      setActionLoading(null);
    }
  };

  if (loading) {
    return (
      <div className={`flex items-center justify-center h-screen ${theme === 'dark' ? 'bg-slate-900' : 'bg-gray-100'}`}>
        <LoadingSpinner size="lg" text="Loading cluster data..." />
      </div>
    );
  }

  const nodes = clusterData?.nodes || {};
  const nodeArray = Object.entries(nodes).map(([id, data]) => ({ id, ...data }));

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

  const totalCpu = nodeArray.reduce((sum, n) => sum + n.cpu_capacity, 0);
  const usedCpu = nodeArray.reduce((sum, n) => sum + (n.cpu_capacity - n.cpu_available), 0);
  const totalPods = nodeArray.reduce((sum, n) => sum + n.pods.length, 0);
  const healthyNodes = nodeArray.filter(n => n.status === 'healthy').length;

  const isDark = theme === 'dark';
  const bgClass = isDark ? 'bg-slate-900' : 'bg-gray-100';
  const cardClass = isDark ? 'bg-slate-800 border-slate-700' : 'bg-white border-gray-300';
  const textClass = isDark ? 'text-white' : 'text-gray-900';
  const textSecondary = isDark ? 'text-slate-400' : 'text-gray-600';
  const inputClass = isDark ? 'bg-slate-800 border-slate-700' : 'bg-white border-gray-300';

  const COLORS = ['#10b981', '#3b82f6', '#f59e0b', '#ef4444', '#8b5cf6'];



  if (!allowed) {
  return (
    <div className="min-h-screen flex items-center justify-center text-red-500 text-xl">
      Access Denied
    </div>
  );
}

  return (
    <div className={`min-h-screen ${isDark ? 'bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900' : 'bg-gradient-to-br from-gray-50 to-gray-200'} ${textClass} p-6`}>
      {/* Header */}
      <div className="mb-8 flex justify-between items-start flex-wrap gap-4">
        <Link href='/'>
        <div>
          <h1 className="text-4xl font-bold mb-2 ">
           CuraNet 
          </h1>
          <p className={textSecondary}>Real-time monitoring with ML predictions & auto-scaling</p>
        </div>
        
        </Link>
        <div className="flex gap-2 flex-wrap">
          {/* Auto-scaler Status */}
          {autoscalerStatus && (
            <div className={`px-3 py-2 rounded-lg ${cardClass} border flex items-center gap-2`}>
              <Zap size={16} className={autoscalerStatus.enabled ? 'text-green-400' : 'text-gray-400'} />
              <span className="text-sm font-medium">
                Auto-Scale: {autoscalerStatus.enabled ? 'ON' : 'OFF'}
              </span>
            </div>
          )}
          
          {/* Theme Toggle */}
          <button
            onClick={() => setTheme(isDark ? 'light' : 'dark')}
            className={`p-2 rounded-lg ${cardClass} border hover:bg-opacity-80 transition-colors`}
          >
            {isDark ? <Sun size={20} /> : <Moon size={20} />}
          </button>
          
          {/* Settings */}
          <button
            onClick={() => setShowSettingsModal(true)}
            className={`px-4 py-2 rounded-lg ${cardClass} border hover:bg-opacity-80 transition-colors flex items-center gap-2`}
          >
            <Settings size={20} />
            Settings
          </button>
          
          {/* Refresh */}
          <button
            onClick={() => fetchData(true)}
            disabled={refreshing}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-700 rounded-lg flex items-center gap-2 transition-colors"
          >
            <RefreshCw className={refreshing ? 'animate-spin' : ''} size={20} />
            Refresh
          </button>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
        <div className={`${cardClass} rounded-lg p-6 border hover:border-blue-500 transition-all`}>
          <div className="flex items-center justify-between">
            <div>
              <p className={textSecondary + " text-sm"}>Total Nodes</p>
              <p className="text-3xl font-bold mt-1">{nodeArray.length}</p>
              <p className="text-green-400 text-sm mt-1">{healthyNodes} healthy</p>
            </div>
            <Server className="text-blue-400" size={40} />
          </div>
        </div>

        <div className={`${cardClass} rounded-lg p-6 border hover:border-green-500 transition-all`}>
          <div className="flex items-center justify-between">
            <div>
              <p className={textSecondary + " text-sm"}>Total Pods</p>
              <p className="text-3xl font-bold mt-1">{totalPods}</p>
              <p className={textSecondary + " text-sm mt-1"}>Running</p>
            </div>
            <Box className="text-green-400" size={40} />
          </div>
        </div>

        <div className={`${cardClass} rounded-lg p-6 border hover:border-purple-500 transition-all`}>
          <div className="flex items-center justify-between">
            <div>
              <p className={textSecondary + " text-sm"}>CPU Usage</p>
              <p className="text-3xl font-bold mt-1">
                {isNaN((usedCpu / totalCpu) * 100) ? '0.0' : ((usedCpu / totalCpu) * 100).toFixed(1)}%
              </p>
              <p className={textSecondary + " text-sm mt-1"}>{usedCpu} / {totalCpu} cores</p>
            </div>
            <Cpu className="text-purple-400" size={40} />
          </div>
        </div>

        <div className={`${cardClass} rounded-lg p-6 border hover:border-yellow-500 transition-all`}>
          <div className="flex items-center justify-between">
            <div>
              <p className={textSecondary + " text-sm"}>Auto-Scaler</p>
              <p className="text-3xl font-bold mt-1">
                {autoscalerStatus?.scaling_history?.length || 0}
              </p>
              <p className={textSecondary + " text-sm mt-1"}>Actions taken</p>
            </div>
            <Zap className="text-yellow-400" size={40} />
          </div>
        </div>
      </div>

      {/* Auto-Scaler Control Panel */}
      {autoscalerStatus && (
        <div className={`${cardClass} rounded-lg p-6 border mb-8`}>
          <div className="flex justify-between items-start mb-4">
            <div>
              <h3 className="text-xl font-semibold flex items-center gap-2">
                <Zap className="text-yellow-400" size={20} />
                Auto-Scaling Control
              </h3>
              <p className={textSecondary + " text-sm mt-1"}>
                Predicted CPU: {autoscalerStatus.current_metrics?.avg_cpu_predicted?.toFixed(1) || 0}% | 
                Current: {autoscalerStatus.current_metrics?.avg_cpu_usage?.toFixed(1) || 0}%
              </p>
            </div>
            <button
              onClick={toggleAutoscaler}
              disabled={actionLoading === 'autoscaler-toggle'}
              className={`px-4 py-2 rounded-lg flex items-center gap-2 transition-colors ${
                autoscalerStatus.enabled 
                  ? 'bg-red-600 hover:bg-red-700' 
                  : 'bg-green-600 hover:bg-green-700'
              } disabled:bg-slate-700`}
            >
              {actionLoading === 'autoscaler-toggle' ? (
                <Loader className="animate-spin" size={16} />
              ) : autoscalerStatus.enabled ? (
                <Pause size={16} />
              ) : (
                <Play size={16} />
              )}
              {autoscalerStatus.enabled ? 'Disable' : 'Enable'}
            </button>
          </div>
          
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div>
              <p className={textSecondary}>Scale Up At</p>
              <p className="font-semibold">{autoscalerStatus.config?.scale_up_threshold}% CPU</p>
            </div>
            <div>
              <p className={textSecondary}>Scale Down At</p>
              <p className="font-semibold">{autoscalerStatus.config?.scale_down_threshold}% CPU</p>
            </div>
            <div>
              <p className={textSecondary}>Node Range</p>
              <p className="font-semibold">
                {autoscalerStatus.config?.min_nodes} - {autoscalerStatus.config?.max_nodes}
              </p>
            </div>
            <div>
              <p className={textSecondary}>Cooldown</p>
              <p className="font-semibold">{autoscalerStatus.config?.cooldown_seconds}s</p>
            </div>
          </div>
        </div>
      )}

      {/* Charts */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
        <div className={`${cardClass} rounded-lg p-6 border`}>
          <h3 className="text-xl font-semibold mb-4 flex items-center gap-2">
            <Activity className="text-blue-400" size={20} />
            CPU Distribution
          </h3>
          {nodeArray.length > 0 ? (
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
                  {nodeArray.map((_, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-[250px] flex items-center justify-center text-slate-500">
              No nodes available
            </div>
          )}
        </div>

        <div className={`${cardClass} rounded-lg p-6 border`}>
          <h3 className="text-xl font-semibold mb-4 flex items-center gap-2">
            <TrendingUp className="text-green-400" size={20} />
            Real-time CPU Usage
          </h3>
          {Object.keys(cpuHistory).length > 0 ? (
            <ResponsiveContainer width="100%" height={250}>
              <LineChart>
                <CartesianGrid strokeDasharray="3 3" stroke={isDark ? '#374151' : '#e5e7eb'} />
                <XAxis dataKey="time" stroke={isDark ? '#9ca3af' : '#6b7280'} tick={{ fontSize: 10 }} />
                <YAxis stroke={isDark ? '#9ca3af' : '#6b7280'} />
                <Tooltip contentStyle={{ backgroundColor: isDark ? '#1e293b' : '#fff', border: `1px solid ${isDark ? '#475569' : '#d1d5db'}` }} />
                <Legend />
                {Object.entries(cpuHistory).slice(0, 5).map(([nodeId, history], idx) => (
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
          ) : (
            <div className="h-[250px] flex items-center justify-center text-slate-500">
              Collecting data...
            </div>
          )}
        </div>
      </div>

      {/* Controls */}
      <div className="flex flex-wrap gap-4 mb-6">
        <div className="flex-1 min-w-[200px]">
          <div className="relative">
            <Search className={`absolute left-3 top-1/2 transform -translate-y-1/2 ${textSecondary}`} size={20} />
            <input
              type="text"
              placeholder="Search nodes..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className={`w-full pl-10 pr-4 py-2 ${inputClass} border rounded-lg focus:outline-none focus:border-blue-500`}
            />
          </div>
        </div>

        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className={`px-4 py-2 ${inputClass} border rounded-lg focus:outline-none focus:border-blue-500`}
        >
          <option value="all">All Status</option>
          <option value="healthy">Healthy</option>
          <option value="unhealthy">Unhealthy</option>
        </select>

        <select
          value={sortBy}
          onChange={(e) => setSortBy(e.target.value)}
          className={`px-4 py-2 ${inputClass} border rounded-lg focus:outline-none focus:border-blue-500`}
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
      <div className={`${cardClass} rounded-lg border overflow-hidden`}>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className={isDark ? 'bg-slate-700' : 'bg-gray-200'}>
              <tr>
                <th className={`px-6 py-3 text-left text-xs font-medium ${textSecondary} uppercase`}>Node ID</th>
                <th className={`px-6 py-3 text-left text-xs font-medium ${textSecondary} uppercase`}>Status</th>
                <th className={`px-6 py-3 text-left text-xs font-medium ${textSecondary} uppercase`}>CPU</th>
                <th className={`px-6 py-3 text-left text-xs font-medium ${textSecondary} uppercase`}>Pods</th>
                <th className={`px-6 py-3 text-left text-xs font-medium ${textSecondary} uppercase`}>ML Prediction</th>
                <th className={`px-6 py-3 text-left text-xs font-medium ${textSecondary} uppercase`}>Actions</th>
              </tr>
            </thead>
            <tbody className={`divide-y ${isDark ? 'divide-slate-700' : 'divide-gray-200'}`}>
              {filteredNodes.map((node) => {
                const cpuUsage = ((node.cpu_capacity - node.cpu_available) / node.cpu_capacity) * 100;
                const prediction = predictions?.predictions?.[node.id];
                const isRemoving = actionLoading === `remove-${node.id}`;
                
                return (
                  <tr key={node.id} className={`${isDark ? 'hover:bg-slate-700' : 'hover:bg-gray-50'} transition-colors cursor-pointer`} onClick={() => setSelectedNode(node)}>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center gap-2">
                        <Server size={16} className="text-blue-400" />
                        <span className="font-mono text-sm">{node.id.slice(0, 12)}...</span>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 py-1 rounded-full text-xs flex items-center gap-1 w-fit ${
                        node.status === 'healthy' ? 'bg-green-900 text-green-300' : 'bg-red-900 text-red-300'
                      }`}>
                        {node.status === 'healthy' ? <CheckCircle size={12} /> : <AlertCircle size={12} />}
                        {node.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          <div className={`flex-1 h-2 ${isDark ? 'bg-slate-600' : 'bg-gray-300'} rounded-full overflow-hidden`}>
                            <div 
                              className={`h-full transition-all ${
                                cpuUsage > 80 ? 'bg-red-500' : cpuUsage > 60 ? 'bg-yellow-500' : 'bg-green-500'
                              }`}
                              style={{ width: `${cpuUsage}%` }}
                            />
                          </div>
                          <span className="text-sm">{cpuUsage.toFixed(0)}%</span>
                        </div>
                        <div className={`text-xs ${textSecondary}`}>
                          {node.cpu_capacity - node.cpu_available} / {node.cpu_capacity} cores
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 py-1 ${isDark ? 'bg-slate-700' : 'bg-gray-200'} rounded text-sm`}>
                        {node.pods.length} pods
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          removeNode(node.id);
                        }}
                        disabled={isRemoving}
                        className="p-2 text-red-400 hover:bg-red-900 disabled:opacity-50 disabled:cursor-not-allowed rounded transition-colors"
                      >
                        {isRemoving ? <Loader className="animate-spin" size={16} /> : <Trash2 size={16} />}
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Settings Modal */}
      {showSettingsModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50" onClick={() => setShowSettingsModal(false)}>
          <div className={`${cardClass} rounded-lg p-6 max-w-2xl w-full border max-h-[90vh] overflow-y-auto`} onClick={(e) => e.stopPropagation()}>
            <h3 className="text-2xl font-bold mb-6">System Settings</h3>
            
            {/* Auto-scaler Config */}
            <div className="mb-6">
              <h4 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <Zap size={18} className="text-yellow-400" />
                Auto-Scaling Configuration
              </h4>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className={`block text-sm ${textSecondary} mb-2`}>Scale Up Threshold (%)</label>
                  <input
                    type="number"
                    value={autoscalerConfig.scale_up_threshold}
                    onChange={(e) => setAutoscalerConfig({...autoscalerConfig, scale_up_threshold: parseInt(e.target.value)})}
                    className={`w-full px-4 py-2 ${inputClass} border rounded focus:outline-none focus:border-blue-500`}
                  />
                </div>
                <div>
                  <label className={`block text-sm ${textSecondary} mb-2`}>Scale Down Threshold (%)</label>
                  <input
                    type="number"
                    value={autoscalerConfig.scale_down_threshold}
                    onChange={(e) => setAutoscalerConfig({...autoscalerConfig, scale_down_threshold: parseInt(e.target.value)})}
                    className={`w-full px-4 py-2 ${inputClass} border rounded focus:outline-none focus:border-blue-500`}
                  />
                </div>
                <div>
                  <label className={`block text-sm ${textSecondary} mb-2`}>Min Nodes</label>
                  <input
                    type="number"
                    value={autoscalerConfig.min_nodes}
                    onChange={(e) => setAutoscalerConfig({...autoscalerConfig, min_nodes: parseInt(e.target.value)})}
                    className={`w-full px-4 py-2 ${inputClass} border rounded focus:outline-none focus:border-blue-500`}
                  />
                </div>
                <div>
                  <label className={`block text-sm ${textSecondary} mb-2`}>Max Nodes</label>
                  <input
                    type="number"
                    value={autoscalerConfig.max_nodes}
                    onChange={(e) => setAutoscalerConfig({...autoscalerConfig, max_nodes: parseInt(e.target.value)})}
                    className={`w-full px-4 py-2 ${inputClass} border rounded focus:outline-none focus:border-blue-500`}
                  />
                </div>
                <div>
                  <label className={`block text-sm ${textSecondary} mb-2`}>New Node CPU</label>
                  <input
                    type="number"
                    value={autoscalerConfig.scale_up_cpu}
                    onChange={(e) => setAutoscalerConfig({...autoscalerConfig, scale_up_cpu: parseInt(e.target.value)})}
                    className={`w-full px-4 py-2 ${inputClass} border rounded focus:outline-none focus:border-blue-500`}
                  />
                </div>
                <div>
                  <label className={`block text-sm ${textSecondary} mb-2`}>Cooldown (seconds)</label>
                  <input
                    type="number"
                    value={autoscalerConfig.cooldown_seconds}
                    onChange={(e) => setAutoscalerConfig({...autoscalerConfig, cooldown_seconds: parseInt(e.target.value)})}
                    className={`w-full px-4 py-2 ${inputClass} border rounded focus:outline-none focus:border-blue-500`}
                  />
                </div>
              </div>
            </div>

            {/* Alert Configuration */}
            <div className="mb-6">
              <h4 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <Bell size={18} className="text-blue-400" />
                Email Alerts
              </h4>
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <span>Enable Alerts</span>
                  <button
                    onClick={toggleAlerts}
                    className={`px-4 py-2 rounded-lg transition-colors ${
                      alertConfig.enabled ? 'bg-green-600 hover:bg-green-700' : 'bg-gray-600 hover:bg-gray-700'
                    }`}
                  >
                    {alertConfig.enabled ? 'Enabled' : 'Disabled'}
                  </button>
                </div>
                <button
                  onClick={sendTestAlert}
                  disabled={actionLoading === 'test-alert'}
                  className="w-full py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-700 rounded transition-colors flex items-center justify-center gap-2"
                >
                  {actionLoading === 'test-alert' ? <Loader className="animate-spin" size={16} /> : <Mail size={16} />}
                  Send Test Alert
                </button>
              </div>
            </div>

            {/* Export Options */}
            <div className="mb-6">
              <h4 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <Download size={18} className="text-green-400" />
                Export & Backup
              </h4>
              <div className="grid grid-cols-2 gap-4">
                <button
                  onClick={() => exportLogs('txt')}
                  disabled={actionLoading === 'export-txt'}
                  className="py-2 bg-gray-600 hover:bg-gray-700 disabled:bg-slate-700 rounded transition-colors flex items-center justify-center gap-2"
                >
                  {actionLoading === 'export-txt' ? <Loader className="animate-spin" size={16} /> : <FileText size={16} />}
                  Logs (TXT)
                </button>
                <button
                  onClick={() => exportLogs('json')}
                  disabled={actionLoading === 'export-json'}
                  className="py-2 bg-gray-600 hover:bg-gray-700 disabled:bg-slate-700 rounded transition-colors flex items-center justify-center gap-2"
                >
                  {actionLoading === 'export-json' ? <Loader className="animate-spin" size={16} /> : <FileText size={16} />}
                  Logs (JSON)
                </button>
                <button
                  onClick={saveClusterConfig}
                  disabled={actionLoading === 'save-config'}
                  className="py-2 bg-green-600 hover:bg-green-700 disabled:bg-slate-700 rounded transition-colors flex items-center justify-center gap-2"
                >
                  {actionLoading === 'save-config' ? <Loader className="animate-spin" size={16} /> : <Upload size={16} />}
                  Save Config
                </button>
                <button
                  onClick={exportClusterConfig}
                  disabled={actionLoading === 'export-config'}
                  className="py-2 bg-green-600 hover:bg-green-700 disabled:bg-slate-700 rounded transition-colors flex items-center justify-center gap-2"
                >
                  {actionLoading === 'export-config' ? <Loader className="animate-spin" size={16} /> : <Download size={16} />}
                  Export Config
                </button>
              </div>
            </div>

            <div className="flex gap-2">
              <button
                onClick={updateAutoscalerConfig}
                disabled={actionLoading === 'update-config'}
                className="flex-1 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-700 rounded transition-colors flex items-center justify-center gap-2"
              >
                {actionLoading === 'update-config' ? <LoadingSpinner size="sm" /> : 'Save Settings'}
              </button>
              <button
                onClick={() => setShowSettingsModal(false)}
                className={`flex-1 py-2 ${isDark ? 'bg-slate-700 hover:bg-slate-600' : 'bg-gray-300 hover:bg-gray-400'} rounded transition-colors`}
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Node Details Modal */}
      {selectedNode && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50" onClick={() => setSelectedNode(null)}>
          <div className={`${cardClass} rounded-lg p-6 max-w-2xl w-full border`} onClick={(e) => e.stopPropagation()}>
            <h3 className="text-2xl font-bold mb-4">Node Details</h3>
            <div className="space-y-4">
              <div>
                <p className={`${textSecondary} text-sm`}>Node ID</p>
                <p className="font-mono">{selectedNode.id}</p>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className={`${textSecondary} text-sm`}>CPU Capacity</p>
                  <p className="text-xl">{selectedNode.cpu_capacity} cores</p>
                </div>
                <div>
                  <p className={`${textSecondary} text-sm`}>Available</p>
                  <p className="text-xl">{selectedNode.cpu_available} cores</p>
                </div>
              </div>
              <div>
                <p className={`${textSecondary} text-sm mb-2`}>Running Pods ({selectedNode.pods.length})</p>
                <div className="space-y-2 max-h-48 overflow-y-auto">
                  {selectedNode.pods.map((pod, idx) => (
                    <div key={idx} className={`${isDark ? 'bg-slate-700' : 'bg-gray-200'} p-3 rounded flex items-center gap-2`}>
                      <Box size={16} className="text-green-400" />
                      <span className="font-mono text-sm">{pod.id?.slice(0, 12) || pod}</span>
                    </div>
                  ))}
                </div>
              </div>
              <button
                onClick={() => setSelectedNode(null)}
                className={`w-full py-2 ${isDark ? 'bg-slate-700 hover:bg-slate-600' : 'bg-gray-300 hover:bg-gray-400'} rounded transition-colors`}
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
          <div className={`${cardClass} rounded-lg p-6 max-w-md w-full border`} onClick={(e) => e.stopPropagation()}>
            <h3 className="text-2xl font-bold mb-4">Add New Node</h3>
            <div className="space-y-4">
              <div>
                <label className={`block text-sm ${textSecondary} mb-2`}>CPU Capacity (cores)</label>
                <input
                  type="number"
                  min="1"
                  max="8"
                  value={nodeCpu}
                  onChange={(e) => {
                  const val = e.target.value
                   setNodeCpu(val == '' ? '' : parseInt(val))}}
                  className={`w-full px-4 py-2 ${inputClass} border rounded focus:outline-none focus:border-blue-500`}
                />
              </div>
              <div className="flex gap-2">
                <button
                  onClick={addNode}
                  disabled={actionLoading === 'add-node'}
                  className="flex-1 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-700 disabled:cursor-not-allowed rounded transition-colors flex items-center justify-center gap-2"
                >
                  {actionLoading === 'add-node' ? <LoadingSpinner size="sm" /> : 'Create Node'}
                </button>
                <button
                  onClick={() => setShowNodeForm(false)}
                  className={`flex-1 py-2 ${isDark ? 'bg-slate-700 hover:bg-slate-600' : 'bg-gray-300 hover:bg-gray-400'} rounded transition-colors`}
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
          <div className={`${cardClass} rounded-lg p-6 max-w-md w-full border`} onClick={(e) => e.stopPropagation()}>
            <h3 className="text-2xl font-bold mb-4">Create New Pod</h3>
            <div className="space-y-4">
              <div>
                <label className={`block text-sm ${textSecondary} mb-2`}>CPU Required (cores)</label>
                <input
                  type="number"
                  min="1"
                  max="6"
                  value={podCpu}
                  onChange={(e) => {
                  const val = e.target.value
                  setPodCpu(val == '' ? '' : parseInt(val))}}
                  className={`w-full px-4 py-2 ${inputClass} border rounded focus:outline-none focus:border-blue-500`}
                />
              </div>
              <div>
                <label className={`block text-sm ${textSecondary} mb-2`}>Container Image</label>
                <input
                  type="text"
                  value={podImage}
                  onChange={(e) => setPodImage(e.target.value)}
                  className={`w-full px-4 py-2 ${inputClass} border rounded focus:outline-none focus:border-blue-500`}
                  placeholder="nginx:latest"
                />
              </div>
              <div className="flex gap-2">
                <button
                  onClick={createPod}
                  disabled={actionLoading === 'create-pod'}
                  className="flex-1 py-2 bg-green-600 hover:bg-green-700 disabled:bg-slate-700 disabled:cursor-not-allowed rounded transition-colors flex items-center justify-center gap-2"
                >
                  {actionLoading === 'create-pod' ? <LoadingSpinner size="sm" /> : 'Create Pod'}
                </button>
                <button
                  onClick={() => setShowPodForm(false)}
                  className={`flex-1 py-2 ${isDark ? 'bg-slate-700 hover:bg-slate-600' : 'bg-gray-300 hover:bg-gray-400'} rounded transition-colors`}
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


