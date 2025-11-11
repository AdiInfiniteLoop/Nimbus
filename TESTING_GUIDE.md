# 🧪 Complete Testing Guide - Cluster Orchestrator

## Testing Checklist Overview

- ✅ Basic Node Operations
- ✅ Pod Scheduling & Management
- ✅ ML Predictions
- ✅ Auto-Scaling
- ✅ Configuration Management
- ✅ Log Export
- ✅ Email Alerts
- ✅ Monitoring & Stats
- ✅ Edge Cases & Error Handling

---

## 🚀 Setup & Prerequisites

```bash
# 1. Start the server
python api_server.py

# Expected output:
# 2. Enable auto-scaling and alerts
curl -X POST http://localhost:5001/autoscaler/enable
curl -X POST http://localhost:5001/alerts/enable

# 3. Create pods
for i in {1..5}; do
  curl -X POST http://localhost:5001/pods \
    -H "Content-Type: application/json" \
    -d '{"cpu_required": 1, "image": "nginx:latest"}'
  sleep 1
done

# 4. Wait for ML predictions (2-3 minutes)
sleep 180

# 5. Check predictions
curl http://localhost:5001/cluster/predictions

# 6. Check if auto-scaling triggered
curl http://localhost:5001/autoscaler/status

# 7. Get cluster status
curl http://localhost:5001/cluster/status

# 8. Export everything
curl http://localhost:5001/predictions/export -o predictions.csv
curl http://localhost:5001/logs/export?format=json -o logs.json
curl -X POST http://localhost:5001/cluster/config/save

# 9. Check alert history
curl http://localhost:5001/alerts/history
```

**Expected:** Complete working system with predictions, auto-scaling, and monitoring

---

### Test 9.2: Failure Recovery Test

```bash
# 1. Create 2 nodes with pods
curl -X POST http://localhost:5001/nodes \
  -H "Content-Type: application/json" \
  -d '{"cpu_capacity": 4}'

NODE_ID_1=$(curl http://localhost:5001/cluster/status | jq -r '.nodes | keys[0]')

curl -X POST http://localhost:5001/nodes \
  -H "Content-Type: application/json" \
  -d '{"cpu_capacity": 4}'

# 2. Create pods on first node
for i in {1..3}; do
  curl -X POST http://localhost:5001/pods \
    -H "Content-Type: application/json" \
    -d '{"cpu_required": 1, "image": "nginx:latest"}'
done

# 3. Check initial state
curl http://localhost:5001/cluster/status

# 4. Simulate node failure
curl -X POST http://localhost:5001/alerts/simulate-failure \
  -H "Content-Type: application/json" \
  -d "{\"node_id\": \"$NODE_ID_1\"}"

# 5. Wait for rescheduling (5-10 seconds)
sleep 10

# 6. Verify pods were rescheduled
curl http://localhost:5001/cluster/status

# 7. Check alert was sent
curl http://localhost:5001/alerts/history
```

**Expected:**
- All 3 pods rescheduled to second node
- Alert sent for node failure
- Node marked as unhealthy

---

### Test 9.3: Load Balancing Test

```bash
# 1. Create 3 nodes
for i in {1..3}; do
  curl -X POST http://localhost:5001/nodes \
    -H "Content-Type: application/json" \
    -d '{"cpu_capacity": 4}'
done

# 2. Create 9 pods (should distribute evenly)
for i in {1..9}; do
  curl -X POST http://localhost:5001/pods \
    -H "Content-Type: application/json" \
    -d '{"cpu_required": 1, "image": "nginx:latest"}'
  sleep 0.5
done

# 3. Check distribution
curl http://localhost:5001/cluster/status | jq '.nodes | to_entries[] | {id: .key, pods: (.value.pods | length)}'
```

**Expected Output:**
```json
{"id": "node-1", "pods": 3}
{"id": "node-2", "pods": 3}
{"id": "node-3", "pods": 3}
```

---

### Test 9.4: High Load Stress Test

```bash
# 1. Create 2 nodes
curl -X POST http://localhost:5001/nodes \
  -H "Content-Type: application/json" \
  -d '{"cpu_capacity": 8}'

curl -X POST http://localhost:5001/nodes \
  -H "Content-Type: application/json" \
  -d '{"cpu_capacity": 8}'

# 2. Rapidly create many pods
for i in {1..20}; do
  curl -X POST http://localhost:5001/pods \
    -H "Content-Type: application/json" \
    -d "{\"cpu_required\": 1, \"image\": \"nginx:latest\"}" &
done
wait

# 3. Check final state
curl http://localhost:5001/cluster/status
```

**Expected:** All or most pods scheduled, some may fail if capacity exceeded

---

### Test 9.5: Configuration Persistence Test

```bash
# 1. Create cluster state
curl -X POST http://localhost:5001/nodes \
  -H "Content-Type: application/json" \
  -d '{"cpu_capacity": 4}'

curl -X POST http://localhost:5001/pods \
  -H "Content-Type: application/json" \
  -d '{"cpu_required": 2, "image": "redis:latest"}'

# 2. Save configuration
curl -X POST http://localhost:5001/cluster/config/save

# 3. Note current state
curl http://localhost:5001/cluster/status > state_before.json

# 4. Restart server (Ctrl+C and restart)
# python api_server.py

# 5. Load configuration
curl -X POST http://localhost:5001/cluster/config/load

# 6. Compare states
curl http://localhost:5001/cluster/status > state_after.json
diff state_before.json state_after.json
```

**Expected:** States should match (note: containers won't persist, but config will)

---

## 🔟 Performance & Benchmark Tests

### Test 10.1: Scheduling Latency

```bash
# Measure time to schedule a pod
time curl -X POST http://localhost:5001/pods \
  -H "Content-Type: application/json" \
  -d '{"cpu_required": 1, "image": "nginx:latest"}'
```

**Expected:** < 200ms

---

### Test 10.2: ML Prediction Latency

```bash
# Wait for model training, then measure prediction time
time curl http://localhost:5001/nodes/$NODE_ID/prediction
```

**Expected:** < 100ms

---

### Test 10.3: Concurrent Request Test

```bash
# Test 10 concurrent pod creations
for i in {1..10}; do
  curl -X POST http://localhost:5001/pods \
    -H "Content-Type: application/json" \
    -d '{"cpu_required": 1, "image": "nginx:latest"}' &
done
wait
```

**Expected:** All requests handled successfully

---

### Test 10.4: Memory Leak Test

```bash
# Monitor memory usage over time
while true; do
  ps aux | grep "python api_server.py" | awk '{print $6}'
  sleep 10
done
```

**Expected:** Memory should remain stable (not continuously increasing)

---

### Test 10.5: Training Performance Test

```bash
# Create multiple nodes and measure training time
for i in {1..5}; do
  curl -X POST http://localhost:5001/nodes \
    -H "Content-Type: application/json" \
    -d '{"cpu_capacity": 4}'
done

# Wait for data collection
sleep 180

# Check training metrics
curl http://localhost:5001/monitoring/stats | jq '.nodes[] | {training_duration_ms: .last_training_duration_ms}'
```

**Expected Output:**
```json
{"training_duration_ms": 850}
{"training_duration_ms": 920}
{"training_duration_ms": 780}
{"training_duration_ms": 1100}
{"training_duration_ms": 950}
```

**Expected:** All < 2000ms

---

## 1️⃣1️⃣ Error Handling Tests

### Test 11.1: Malformed JSON

```bash
curl -X POST http://localhost:5001/nodes \
  -H "Content-Type: application/json" \
  -d '{cpu_capacity: 4}'  # Missing quotes
```

**Expected Response:**
```json
{
  "error": "No data provided"
}
```

**Status Code:** 400

---

### Test 11.2: Wrong HTTP Method

```bash
curl -X GET http://localhost:5001/nodes \
  -H "Content-Type: application/json" \
  -d '{"cpu_capacity": 4}'
```

**Expected Response:**
```json
{
  "error": "Method not allowed"
}
```

**Status Code:** 405

---

### Test 11.3: Missing Content-Type

```bash
curl -X POST http://localhost:5001/nodes \
  -d '{"cpu_capacity": 4}'
```

**Expected:** Should still work (Flask handles this gracefully)

---

### Test 11.4: Docker Connection Lost

```bash
# Stop Docker Desktop
# Try to create a node

curl -X POST http://localhost:5001/nodes \
  -H "Content-Type: application/json" \
  -d '{"cpu_capacity": 4}'
```

**Expected Response:**
```json
{
  "error": "Docker API error: ..."
}
```

---

### Test 11.5: Numeric Overflow

```bash
curl -X POST http://localhost:5001/nodes \
  -H "Content-Type: application/json" \
  -d '{"cpu_capacity": 999999999999}'
```

**Expected Response:**
```json
{
  "error": "CPU capacity too high: 999999999999 (maximum is 8)"
}
```

---

### Test 11.6: Negative Values

```bash
curl -X POST http://localhost:5001/pods \
  -H "Content-Type: application/json" \
  -d '{"cpu_required": -5, "image": "nginx:latest"}'
```

**Expected Response:**
```json
{
  "error": "CPU requirement must be positive"
}
```

---

### Test 11.7: SQL Injection Attempt (N/A but test anyway)

```bash
curl -X DELETE "http://localhost:5001/nodes/'; DROP TABLE nodes; --"
```

**Expected Response:**
```json
{
  "error": "Node not found"
}
```

---

### Test 11.8: XSS Attempt in Node ID

```bash
curl -X DELETE "http://localhost:5001/nodes/<script>alert('xss')</script>"
```

**Expected Response:**
```json
{
  "error": "Node not found"
}
```

---

## 1️⃣2️⃣ Edge Case Scenarios

### Test 12.1: Zero Nodes, Create Pod

```bash
# Ensure no nodes exist
curl http://localhost:5001/cluster/status

# Try to create pod
curl -X POST http://localhost:5001/pods \
  -H "Content-Type: application/json" \
  -d '{"cpu_required": 1, "image": "nginx:latest"}'
```

**Expected Response:**
```json
{
  "error": "No nodes available in the cluster"
}
```

---

### Test 12.2: All Nodes Unhealthy

```bash
# Create nodes
curl -X POST http://localhost:5001/nodes \
  -H "Content-Type: application/json" \
  -d '{"cpu_capacity": 4}'

# Simulate all nodes failing
curl -X POST http://localhost:5001/alerts/simulate-failure \
  -H "Content-Type: application/json" \
  -d '{"node_id": "..."}'

# Try to create pod
curl -X POST http://localhost:5001/pods \
  -H "Content-Type: application/json" \
  -d '{"cpu_required": 1, "image": "nginx:latest"}'
```

**Expected Response:**
```json
{
  "error": "No node has 1 CPU cores available. Current nodes are at capacity."
}
```

---

### Test 12.3: Pod Larger Than Any Node

```bash
# Create node with 2 CPU
curl -X POST http://localhost:5001/nodes \
  -H "Content-Type: application/json" \
  -d '{"cpu_capacity": 2}'

# Try to create pod requiring 4 CPU
curl -X POST http://localhost:5001/pods \
  -H "Content-Type: application/json" \
  -d '{"cpu_required": 4, "image": "nginx:latest"}'
```

**Expected Response:**
```json
{
  "error": "No node has 4 CPU cores available. Current nodes are at capacity."
}
```

---

### Test 12.4: Fractional CPU (Invalid)

```bash
curl -X POST http://localhost:5001/pods \
  -H "Content-Type: application/json" \
  -d '{"cpu_required": 1.5, "image": "nginx:latest"}'
```

**Expected:** Should convert to integer (1) or reject

---

### Test 12.5: Empty Image Name

```bash
curl -X POST http://localhost:5001/pods \
  -H "Content-Type: application/json" \
  -d '{"cpu_required": 1, "image": ""}'
```

**Expected:** Uses default image or rejects

---

### Test 12.6: Invalid Docker Image

```bash
curl -X POST http://localhost:5001/pods \
  -H "Content-Type: application/json" \
  -d '{"cpu_required": 1, "image": "nonexistent-image:9999"}'
```

**Expected Response:**
```json
{
  "error": "Failed to create pod container: ..."
}
```

---

### Test 12.7: Rapid Add/Remove Nodes

```bash
# Rapidly add and remove nodes
for i in {1..5}; do
  NODE_ID=$(curl -s -X POST http://localhost:5001/nodes \
    -H "Content-Type: application/json" \
    -d '{"cpu_capacity": 4}' | jq -r '.node_id')
  
  curl -X DELETE http://localhost:5001/nodes/$NODE_ID
done
```

**Expected:** All operations succeed, no crashes

---

### Test 12.8: Prediction Before Training

```bash
# Immediately after creating node
curl -X POST http://localhost:5001/nodes \
  -H "Content-Type: application/json" \
  -d '{"cpu_capacity": 4}'

NODE_ID=$(curl -s http://localhost:5001/cluster/status | jq -r '.nodes | keys[0]')

# Try to get prediction immediately
curl http://localhost:5001/nodes/$NODE_ID/prediction
```

**Expected Response:**
```json
{
  "error": "No prediction available"
}
```

---

### Test 12.9: Export With No Data

```bash
# Fresh start, try to export
curl http://localhost:5001/predictions/export
```

**Expected Response:**
```json
{
  "error": "No data available for export"
}
```

**Status Code:** 404

---

### Test 12.10: Concurrent Node Removal

```bash
# Create node
NODE_ID=$(curl -s -X POST http://localhost:5001/nodes \
  -H "Content-Type: application/json" \
  -d '{"cpu_capacity": 4}' | jq -r '.node_id')

# Try to remove same node twice concurrently
curl -X DELETE http://localhost:5001/nodes/$NODE_ID &
curl -X DELETE http://localhost:5001/nodes/$NODE_ID &
wait
```

**Expected:** One succeeds, one returns error

---

## 1️⃣3️⃣ Security Tests

### Test 13.1: CORS Headers

```bash
curl -H "Origin: http://example.com" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: Content-Type" \
  -X OPTIONS http://localhost:5001/nodes
```

**Expected:** CORS headers present in response

---

### Test 13.2: Rate Limiting (if implemented)

```bash
# Send 100 requests rapidly
for i in {1..100}; do
  curl http://localhost:5001/cluster/status &
done
wait
```

**Expected:** All succeed (no rate limiting currently)

---

### Test 13.3: Large Payload

```bash
# Try to send very large JSON
python3 << 'EOF'
import requests
large_payload = {"cpu_capacity": 4, "extra": "x" * 1000000}
r = requests.post("http://localhost:5001/nodes", json=large_payload)
print(r.status_code, r.text)
EOF
```

**Expected:** Handled gracefully

---

## 1️⃣4️⃣ Cleanup & Verification

### Test 14.1: Clean Shutdown

```bash
# Stop server gracefully (Ctrl+C)
# Check for any orphaned containers

docker ps -a | grep "node-\|pod-"
```

**Expected:** Containers still exist (they're not auto-removed)

---

### Test 14.2: Manual Cleanup

```bash
# Remove all created containers
docker ps -a | grep "node-\|pod-" | awk '{print $1}' | xargs docker rm -f

# Verify
docker ps -a | grep "node-\|pod-"
```

**Expected:** No output (all cleaned up)

---

### Test 14.3: Verify Logs Generated

```bash
ls -lh orchestrator.log
cat orchestrator.log | wc -l
```

**Expected:** Log file exists with content

---

### Test 14.4: Verify Exports Generated

```bash
ls -lh *.csv *.json *.txt 2>/dev/null
```

**Expected:** Export files if tests were run

---

## 📊 Test Summary Template

```bash
#!/bin/bash
# Complete test suite runner

echo "=== Cluster Orchestrator Test Suite ==="
echo ""

# Test counters
TOTAL=0
PASSED=0
FAILED=0

# Test function
test_endpoint() {
  TOTAL=$((TOTAL + 1))
  echo -n "Test $TOTAL: $1... "
  
  RESPONSE=$(eval $2 2>&1)
  EXPECTED=$3
  
  if echo "$RESPONSE" | grep -q "$EXPECTED"; then
    echo "✅ PASSED"
    PASSED=$((PASSED + 1))
  else
    echo "❌ FAILED"
    echo "Expected: $EXPECTED"
    echo "Got: $RESPONSE"
    FAILED=$((FAILED + 1))
  fi
}

# Run tests
test_endpoint "Add Node" \
  "curl -s -X POST http://localhost:5001/nodes -H 'Content-Type: application/json' -d '{\"cpu_capacity\": 4}'" \
  "node_id"

test_endpoint "Get Status" \
  "curl -s http://localhost:5001/cluster/status" \
  "nodes"

test_endpoint "Invalid CPU" \
  "curl -s -X POST http://localhost:5001/nodes -H 'Content-Type: application/json' -d '{\"cpu_capacity\": 0}'" \
  "error"

# Add more tests...

echo ""
echo "=== Test Results ==="
echo "Total: $TOTAL"
echo "Passed: $PASSED ✅"
echo "Failed: $FAILED ❌"
echo "Success Rate: $((PASSED * 100 / TOTAL))%"
```

---

## 🎯 Expected Overall Results

After running all tests:

**Successful Operations:**
- ✅ 50+ endpoint tests passing
- ✅ 20+ edge case tests handled
- ✅ 10+ integration tests working
- ✅ All error cases caught properly
- ✅ No crashes or memory leaks
- ✅ Performance within expected ranges

**Known Limitations:**
- Email alerts are simulated (logged, not actually sent)
- Container persistence requires Docker state
- ML predictions need 2-3 minutes of data

**System Health Indicators:**
- No memory leaks
- Response times < 200ms
- ML training < 2 seconds/node
- Auto-scaling responds within 1 minute
- All exports generate successfully

---

## 📝 Testing Checklist for Demo/Presentation

```
□ Server starts without errors
□ Can add nodes successfully
□ Can create pods successfully
□ ML predictions appear after 3 minutes
□ Auto-scaler can be enabled/disabled
□ Auto-scaler creates nodes under high load
□ Logs can be exported (TXT & JSON)
□ Cluster config can be saved/exported
□ Email alerts are triggered
□ Dashboard loads and displays data
□ Theme toggle works
□ Settings modal functions properly
□ All critical APIs respond correctly
□ No crashes during stress testing
□ Graceful error handling demonstrated
```

---

**This comprehensive testing guide covers every endpoint, edge case, and integration scenario. Use it to thoroughly validate your project before demonstration!** 🎓✅025-11-11 10:00:00 - INFO - Successfully connected to Docker
# 2025-11-11 10:00:00 - INFO - Health monitoring thread started
# 2025-11-11 10:00:00 - INFO - ML predictor started
# 2025-11-11 10:00:00 - INFO - Auto-scaler initialized (disabled by default)
# ==================================================
# 🚀 Cluster Orchestrator API Server Ready
# ==================================================
#  * Running on http://0.0.0.0:5001

# 2. Verify Docker is running
docker ps

# Expected: List of running containers (may be empty initially)
```

---

## 1️⃣ Node Management Tests

### Test 1.1: Add Node (Success)

```bash
curl -X POST http://localhost:5001/nodes \
  -H "Content-Type: application/json" \
  -d '{"cpu_capacity": 4}'
```

**Expected Response:**
```json
{
  "node_id": "a1b2c3d4-5678-90ab-cdef-1234567890ab",
  "message": "Node added successfully"
}
```

**Verify:**
```bash
docker ps | grep node-

# Expected: One container named node-a1b2c3d4...
```

---

### Test 1.2: Add Node (Edge Case - Invalid CPU)

```bash
# Test with 0 CPU
curl -X POST http://localhost:5001/nodes \
  -H "Content-Type: application/json" \
  -d '{"cpu_capacity": 0}'
```

**Expected Response:**
```json
{
  "error": "CPU capacity must be positive"
}
```

**Status Code:** 400

---

### Test 1.3: Add Node (Edge Case - Exceeds Max)

```bash
# Test with CPU > MAX_NODE_CPU (8)
curl -X POST http://localhost:5001/nodes \
  -H "Content-Type: application/json" \
  -d '{"cpu_capacity": 10}'
```

**Expected Response:**
```json
{
  "error": "Maximum CPU capacity per node is 8 cores"
}
```

**Status Code:** 400

---

### Test 1.4: Add Node (Edge Case - Exceeds System Capacity)

```bash
# Add multiple nodes until system capacity is reached
# Assuming 8-core system, add 2 nodes with 4 cores each (total 8)
curl -X POST http://localhost:5001/nodes \
  -H "Content-Type: application/json" \
  -d '{"cpu_capacity": 4}'

curl -X POST http://localhost:5001/nodes \
  -H "Content-Type: application/json" \
  -d '{"cpu_capacity": 4}'

# Try to add one more (should fail)
curl -X POST http://localhost:5001/nodes \
  -H "Content-Type: application/json" \
  -d '{"cpu_capacity": 4}'
```

**Expected Response:**
```json
{
  "error": "Cannot add node: Total CPU capacity (12) would exceed system capacity (8)"
}
```

---

### Test 1.5: Add Node (Edge Case - Missing Parameter)

```bash
curl -X POST http://localhost:5001/nodes \
  -H "Content-Type: application/json" \
  -d '{}'
```

**Expected Response:**
```json
{
  "error": "CPU capacity is required"
}
```

**Status Code:** 400

---

### Test 1.6: Add Node (Edge Case - Invalid JSON)

```bash
curl -X POST http://localhost:5001/nodes \
  -H "Content-Type: application/json" \
  -d 'invalid json'
```

**Expected Response:**
```json
{
  "error": "No data provided"
}
```

**Status Code:** 400

---

### Test 1.7: Get Cluster Status

```bash
curl http://localhost:5001/cluster/status
```

**Expected Response:**
```json
{
  "nodes": {
    "a1b2c3d4-5678-90ab-cdef-1234567890ab": {
      "cpu_capacity": 4,
      "cpu_available": 4,
      "status": "healthy",
      "health_metrics": {
        "cpu_usage_percent": 0,
        "memory_usage_percent": 12.5,
        "running_pods": 0,
        "container_status": "running"
      },
      "health_status": {
        "conditions": {
          "heartbeat": true,
          "memory": true,
          "container": true,
          "pods": true
        }
      },
      "pods": [],
      "last_heartbeat": "2025-11-11T10:05:00"
    }
  }
}
```

---

### Test 1.8: Remove Node (Success)

```bash
# Get node_id from cluster status first
NODE_ID="a1b2c3d4-5678-90ab-cdef-1234567890ab"

curl -X DELETE http://localhost:5001/nodes/$NODE_ID
```

**Expected Response:**
```json
{
  "message": "Node a1b2c3d4-5678-90ab-cdef-1234567890ab removed successfully",
  "rescheduled_pods": 0,
  "failed_pods": 0
}
```

---

### Test 1.9: Remove Node (Edge Case - Invalid Node ID)

```bash
curl -X DELETE http://localhost:5001/nodes/invalid-node-id
```

**Expected Response:**
```json
{
  "error": "Node not found"
}
```

**Status Code:** 404

---

### Test 1.10: Remove Node (With Pods - Rescheduling)

```bash
# Setup: Create node and pods first
curl -X POST http://localhost:5001/nodes \
  -H "Content-Type: application/json" \
  -d '{"cpu_capacity": 4}'

# Create another node for rescheduling
curl -X POST http://localhost:5001/nodes \
  -H "Content-Type: application/json" \
  -d '{"cpu_capacity": 4}'

# Create a pod
curl -X POST http://localhost:5001/pods \
  -H "Content-Type: application/json" \
  -d '{"cpu_required": 1, "image": "nginx:latest"}'

# Get first node ID and remove it
curl -X DELETE http://localhost:5001/nodes/$NODE_ID
```

**Expected Response:**
```json
{
  "message": "Node ... removed successfully",
  "rescheduled_pods": 1,
  "failed_pods": 0
}
```

---

## 2️⃣ Pod Management Tests

### Test 2.1: Create Pod (Success)

```bash
# First, ensure at least one node exists
curl -X POST http://localhost:5001/nodes \
  -H "Content-Type: application/json" \
  -d '{"cpu_capacity": 4}'

# Create pod
curl -X POST http://localhost:5001/pods \
  -H "Content-Type: application/json" \
  -d '{"cpu_required": 2, "image": "nginx:latest"}'
```

**Expected Response:**
```json
{
  "pod_id": "pod123-456-789",
  "message": "Pod scheduled successfully",
  "node_id": "a1b2c3d4-5678-90ab-cdef-1234567890ab",
  "image": "nginx:latest",
  "access_url": "http://localhost:12345"
}
```

**Verify:**
```bash
docker ps | grep pod-

# Expected: Container named pod-pod123...
```

---

### Test 2.2: Create Pod (Edge Case - No Nodes)

```bash
# Remove all nodes first
# Then try to create pod

curl -X POST http://localhost:5001/pods \
  -H "Content-Type: application/json" \
  -d '{"cpu_required": 2, "image": "nginx:latest"}'
```

**Expected Response:**
```json
{
  "error": "No nodes available in the cluster"
}
```

**Status Code:** 400

---

### Test 2.3: Create Pod (Edge Case - Insufficient Resources)

```bash
# Create node with 2 CPU
curl -X POST http://localhost:5001/nodes \
  -H "Content-Type: application/json" \
  -d '{"cpu_capacity": 2}'

# Try to create pod requiring 4 CPU
curl -X POST http://localhost:5001/pods \
  -H "Content-Type: application/json" \
  -d '{"cpu_required": 4, "image": "nginx:latest"}'
```

**Expected Response:**
```json
{
  "error": "No node has 4 CPU cores available. Current nodes are at capacity."
}
```

**Status Code:** 400

---

### Test 2.4: Create Pod (Edge Case - Exceeds Max Pod CPU)

```bash
curl -X POST http://localhost:5001/pods \
  -H "Content-Type: application/json" \
  -d '{"cpu_required": 10, "image": "nginx:latest"}'
```

**Expected Response:**
```json
{
  "error": "Maximum CPU requirement per pod is 6 cores"
}
```

**Status Code:** 400

---

### Test 2.5: Create Pod (Edge Case - Invalid CPU)

```bash
curl -X POST http://localhost:5001/pods \
  -H "Content-Type: application/json" \
  -d '{"cpu_required": -1, "image": "nginx:latest"}'
```

**Expected Response:**
```json
{
  "error": "CPU requirement must be positive"
}
```

**Status Code:** 400

---

### Test 2.6: Create Pod (Edge Case - Missing CPU)

```bash
curl -X POST http://localhost:5001/pods \
  -H "Content-Type: application/json" \
  -d '{"image": "nginx:latest"}'
```

**Expected Response:**
```json
{
  "error": "CPU requirement is required"
}
```

**Status Code:** 400

---

### Test 2.7: Create Pod (Custom Image)

```bash
curl -X POST http://localhost:5001/pods \
  -H "Content-Type: application/json" \
  -d '{"cpu_required": 1, "image": "redis:latest"}'
```

**Expected Response:**
```json
{
  "pod_id": "pod-xyz-123",
  "message": "Pod scheduled successfully",
  "node_id": "...",
  "image": "redis:latest",
  "access_url": "http://localhost:15678"
}
```

---

### Test 2.8: Create Multiple Pods (Capacity Test)

```bash
# Create node with 4 CPU
curl -X POST http://localhost:5001/nodes \
  -H "Content-Type: application/json" \
  -d '{"cpu_capacity": 4}'

# Create 4 pods with 1 CPU each (should succeed)
for i in {1..4}; do
  curl -X POST http://localhost:5001/pods \
    -H "Content-Type: application/json" \
    -d '{"cpu_required": 1, "image": "nginx:latest"}'
  echo ""
done

# Try to create 5th pod (should fail)
curl -X POST http://localhost:5001/pods \
  -H "Content-Type: application/json" \
  -d '{"cpu_required": 1, "image": "nginx:latest"}'
```

**Expected for 5th Pod:**
```json
{
  "error": "No node has 1 CPU cores available. Current nodes are at capacity."
}
```

---

## 3️⃣ ML Predictions Tests

### Test 3.1: Get Predictions (Initial - Training)

```bash
# Wait 30 seconds after creating nodes, then:
curl http://localhost:5001/cluster/predictions
```

**Expected Response (if training):**
```json
{
  "predictions": {},
  "prediction_interval_seconds": 30
}
```

---

### Test 3.2: Get Predictions (After Training)

```bash
# Wait 2-3 minutes for data collection and training
curl http://localhost:5001/cluster/predictions
```

**Expected Response:**
```json
{
  "predictions": {
    "node-id-1": {
      "predicted_cpu": 25.3,
      "timestamp": "2025-11-11T10:10:00",
      "current_cpu": 20.0,
      "confidence": 0.87,
      "freshness": {
        "data_age_seconds": 2.5,
        "model_age_seconds": 45.0,
        "is_stale": false,
        "last_training": "2025-11-11T10:09:15"
      },
      "quality": {
        "r2_score": 0.87,
        "mae": 4.2,
        "rmse": 5.8,
        "samples": 85,
        "is_accurate": true
      }
    }
  },
  "prediction_interval_seconds": 30
}
```

---

### Test 3.3: Get Single Node Prediction

```bash
NODE_ID="a1b2c3d4-5678-90ab-cdef-1234567890ab"
curl http://localhost:5001/nodes/$NODE_ID/prediction
```

**Expected Response:**
```json
{
  "predicted_cpu": 25.3,
  "timestamp": "2025-11-11T10:10:00",
  "current_cpu": 20.0,
  "confidence": 0.87,
  "freshness": {
    "data_age_seconds": 2.5,
    "model_age_seconds": 45.0,
    "is_stale": false
  },
  "quality": {
    "r2_score": 0.87,
    "mae": 4.2,
    "is_accurate": true
  }
}
```

---

### Test 3.4: Get Prediction (Edge Case - Invalid Node)

```bash
curl http://localhost:5001/nodes/invalid-node-id/prediction
```

**Expected Response:**
```json
{
  "error": "No prediction available"
}
```

**Status Code:** 404

---

### Test 3.5: Export Predictions (CSV)

```bash
curl http://localhost:5001/predictions/export -o predictions.csv

# Verify file
cat predictions.csv
```

**Expected Output:**
```csv
node_id,timestamp,cpu_percent,memory_percent,pod_count,predicted_cpu,prediction_error,model_r2,model_mae,model_rmse,training_time_ms,data_age_seconds,model_age_seconds
node-id-1,2025-11-11T10:10:00,20.0,15.5,2,25.3,5.3,0.87,4.2,5.8,1250,2.5,45.0
...
```

---

### Test 3.6: Export Predictions (Edge Case - No Data)

```bash
# Try to export immediately after starting (before training)
curl http://localhost:5001/predictions/export
```

**Expected Response:**
```json
{
  "error": "No data available for export"
}
```

**Status Code:** 404

---

## 4️⃣ Auto-Scaling Tests

### Test 4.1: Get Auto-Scaler Status (Initial)

```bash
curl http://localhost:5001/autoscaler/status
```

**Expected Response:**
```json
{
  "enabled": false,
  "config": {
    "scale_up_threshold": 75,
    "scale_down_threshold": 30,
    "min_nodes": 1,
    "max_nodes": 10,
    "scale_up_cpu": 4,
    "cooldown_seconds": 60
  },
  "last_action": null,
  "can_scale_now": true,
  "current_metrics": {
    "avg_cpu_usage": 0.0,
    "avg_cpu_predicted": 0.0,
    "total_nodes": 0,
    "healthy_nodes": 0,
    "total_pods": 0
  },
  "scaling_history": [],
  "recommendations": {
    "should_scale_up": false,
    "should_scale_down": false
  }
}
```

---

### Test 4.2: Enable Auto-Scaler

```bash
curl -X POST http://localhost:5001/autoscaler/enable
```

**Expected Response:**
```json
{
  "message": "Auto-scaling enabled",
  "status": "enabled"
}
```

---

### Test 4.3: Disable Auto-Scaler

```bash
curl -X POST http://localhost:5001/autoscaler/disable
```

**Expected Response:**
```json
{
  "message": "Auto-scaling disabled",
  "status": "disabled"
}
```

---

### Test 4.4: Update Auto-Scaler Config

```bash
curl -X POST http://localhost:5001/autoscaler/config \
  -H "Content-Type: application/json" \
  -d '{
    "scale_up_threshold": 70,
    "scale_down_threshold": 25,
    "min_nodes": 2,
    "max_nodes": 8,
    "scale_up_cpu": 4,
    "cooldown_seconds": 45
  }'
```

**Expected Response:**
```json
{
  "message": "Configuration updated",
  "config": {
    "scale_up_threshold": 70,
    "scale_down_threshold": 25,
    "min_nodes": 2,
    "max_nodes": 8,
    "scale_up_cpu": 4,
    "cooldown_seconds": 45
  }
}
```

---

### Test 4.5: Get Auto-Scaler Config

```bash
curl http://localhost:5001/autoscaler/config
```

**Expected Response:**
```json
{
  "scale_up_threshold": 70,
  "scale_down_threshold": 25,
  "min_nodes": 2,
  "max_nodes": 8,
  "scale_up_cpu": 4,
  "cooldown_seconds": 45
}
```

---

### Test 4.6: Trigger Auto-Scale Up

```bash
# Setup: Create node and enable auto-scaler
curl -X POST http://localhost:5001/nodes \
  -H "Content-Type: application/json" \
  -d '{"cpu_capacity": 4}'

curl -X POST http://localhost:5001/autoscaler/enable

# Create multiple pods to push CPU usage high
for i in {1..3}; do
  curl -X POST http://localhost:5001/pods \
    -H "Content-Type: application/json" \
    -d '{"cpu_required": 1, "image": "nginx:latest"}'
done

# Wait 2-3 minutes for ML model to predict high usage
# Check if new node was added automatically
curl http://localhost:5001/cluster/status
```

**Expected:** A new node should be automatically created

---

### Test 4.7: Get Scaling History

```bash
curl http://localhost:5001/autoscaler/history?limit=10
```

**Expected Response:**
```json
{
  "history": [
    {
      "timestamp": "2025-11-11T10:15:00",
      "action": "scale_up",
      "reason": "Predicted CPU 78.5%",
      "node_id": "new-node-id",
      "nodes_before": 1,
      "nodes_after": 2
    }
  ],
  "total": 1
}
```

---

### Test 4.8: Auto-Scale (Edge Case - At Max Nodes)

```bash
# Set max_nodes to current count
curl -X POST http://localhost:5001/autoscaler/config \
  -H "Content-Type: application/json" \
  -d '{"max_nodes": 1}'

# Try to trigger scale up (should not add nodes)
# Check logs for message
tail -f orchestrator.log
```

**Expected Log:**
```
Cannot scale up: at max nodes (1)
```

---

### Test 4.9: Auto-Scale (Edge Case - At Min Nodes)

```bash
# Set min_nodes to current count
curl -X POST http://localhost:5001/autoscaler/config \
  -H "Content-Type: application/json" \
  -d '{"min_nodes": 2}'

# Try to trigger scale down (should not remove nodes)
# Check logs
tail -f orchestrator.log
```

**Expected Log:**
```
Cannot scale down: at min nodes (2)
```

---

### Test 4.10: Auto-Scale (Cooldown Period)

```bash
# Trigger scale action
# Immediately try to trigger another (should be blocked)

# Check status
curl http://localhost:5001/autoscaler/status | grep can_scale_now
```

**Expected:**
```json
"can_scale_now": false
```

---

## 5️⃣ Configuration Management Tests

### Test 5.1: Save Cluster Config

```bash
curl -X POST http://localhost:5001/cluster/config/save
```

**Expected Response:**
```json
{
  "message": "Configuration saved",
  "filepath": "cluster_config.json"
}
```

**Verify:**
```bash
cat cluster_config.json
```

**Expected Output:**
```json
{
  "timestamp": "2025-11-11T10:20:00",
  "version": "1.0",
  "nodes": {
    "node-id-1": {
      "cpu_capacity": 4,
      "cpu_available": 2,
      "status": "healthy",
      "pods": ["pod-1", "pod-2"]
    }
  },
  "pods": {
    "pod-1": {
      "node_id": "node-id-1",
      "cpu_required": 1,
      "image": "nginx:latest",
      "status": "running"
    }
  }
}
```

---

### Test 5.2: Load Cluster Config

```bash
curl -X POST http://localhost:5001/cluster/config/load
```

**Expected Response:**
```json
{
  "message": "Configuration loaded",
  "config": {
    "timestamp": "2025-11-11T10:20:00",
    "version": "1.0",
    "nodes": {...},
    "pods": {...}
  },
  "note": "This is a preview. Use /cluster/config/apply to apply it."
}
```

---

### Test 5.3: Export Cluster Config

```bash
curl http://localhost:5001/cluster/config/export -o cluster_export.json

# Verify
cat cluster_export.json
```

**Expected:** JSON file with complete cluster state

---

### Test 5.4: Load Config (Edge Case - File Not Found)

```bash
# Delete config file first
rm cluster_config.json

curl -X POST http://localhost:5001/cluster/config/load
```

**Expected Response:**
```json
{
  "error": "Failed to load configuration"
}
```

**Status Code:** 500

---

## 6️⃣ Log Export Tests

### Test 6.1: Export Logs (TXT)

```bash
curl "http://localhost:5001/logs/export?format=txt" -o logs.txt

# Verify
head -20 logs.txt
```

**Expected Output:**
```
=== Cluster Orchestrator System Logs ===
Exported: 2025-11-11T10:25:00
Total Entries: 1523
==================================================

2025-11-11 10:00:00 - INFO - Successfully connected to Docker
2025-11-11 10:00:05 - INFO - Node added: node-id-1
2025-11-11 10:01:20 - INFO - Pod scheduled: pod-id-1
...
```

---

### Test 6.2: Export Logs (JSON)

```bash
curl "http://localhost:5001/logs/export?format=json" -o logs.json

# Verify
cat logs.json | head -30
```

**Expected Output:**
```json
{
  "exported_at": "2025-11-11T10:25:00",
  "total_logs": 1523,
  "logs": [
    "2025-11-11 10:00:00 - INFO - Successfully connected to Docker\n",
    "2025-11-11 10:00:05 - INFO - Node added: node-id-1\n",
    ...
  ]
}
```

---

### Test 6.3: Export Logs (Edge Case - Invalid Format)

```bash
curl "http://localhost:5001/logs/export?format=xml"
```

**Expected:** Defaults to TXT format

---

## 7️⃣ Email Alerts Tests

### Test 7.1: Get Alert Config

```bash
curl http://localhost:5001/alerts/config
```

**Expected Response:**
```json
{
  "enabled": false,
  "config": {
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "sender_email": "",
    "sender_password": "",
    "recipient_emails": []
  }
}
```

---

### Test 7.2: Enable Alerts

```bash
curl -X POST http://localhost:5001/alerts/enable
```

**Expected Response:**
```json
{
  "message": "Email alerts enabled",
  "status": "enabled"
}
```

---

### Test 7.3: Update Alert Config

```bash
curl -X POST http://localhost:5001/alerts/config \
  -H "Content-Type: application/json" \
  -d '{
    "sender_email": "admin@example.com",
    "recipient_emails": ["ops@example.com", "admin@example.com"]
  }'
```

**Expected Response:**
```json
{
  "message": "Alert configuration updated"
}
```

---

### Test 7.4: Send Test Alert

```bash
curl -X POST http://localhost:5001/alerts/test
```

**Expected Response:**
```json
{
  "message": "Test alert sent",
  "success": true
}
```

**Check logs:**
```bash
tail -f orchestrator.log
```

**Expected Log:**
```
2025-11-11 10:30:00 - INFO - 📧 EMAIL ALERT [INFO]: Test Alert
2025-11-11 10:30:00 - INFO -    To: ops@example.com, admin@example.com
2025-11-11 10:30:00 - INFO -    Message: This is a test alert from the Cluster Orchestrator
```

---

### Test 7.5: Simulate Node Failure

```bash
# First create a node
curl -X POST http://localhost:5001/nodes \
  -H "Content-Type: application/json" \
  -d '{"cpu_capacity": 4}'

# Get node ID, then simulate failure
NODE_ID="node-id-here"
curl -X POST http://localhost:5001/alerts/simulate-failure \
  -H "Content-Type: application/json" \
  -d "{\"node_id\": \"$NODE_ID\"}"
```

**Expected Response:**
```json
{
  "message": "Node ... marked as failed",
  "alert_sent": true
}
```

**Check logs:**
```
2025-11-11 10:32:00 - INFO - 📧 EMAIL ALERT [CRITICAL]: 🚨 Node Failure: node-id
2025-11-11 10:32:00 - INFO -    Message: Node Failure Detected...
```

---

### Test 7.6: Get Alert History

```bash
curl http://localhost:5001/alerts/history?limit=10
```

**Expected Response:**
```json
{
  "history": [
    {
      "timestamp": "2025-11-11T10:32:00",
      "subject": "🚨 Node Failure: node-id",
      "message": "Node Failure Detected...",
      "severity": "CRITICAL",
      "sent": true
    },
    {
      "timestamp": "2025-11-11T10:30:00",
      "subject": "Test Alert",
      "message": "This is a test alert...",
      "severity": "INFO",
      "sent": true
    }
  ],
  "total": 2
}
```

---

### Test 7.7: Simulate Failure (Edge Case - Invalid Node)

```bash
curl -X POST http://localhost:5001/alerts/simulate-failure \
  -H "Content-Type: application/json" \
  -d '{"node_id": "invalid-node-id"}'
```

**Expected Response:**
```json
{
  "error": "Invalid node ID"
}
```

**Status Code:** 400

---

## 8️⃣ Monitoring Stats Tests

### Test 8.1: Get Monitoring Stats

```bash
curl http://localhost:5001/monitoring/stats
```

**Expected Response:**
```json
{
  "total_nodes": 2,
  "trained_models": 2,
  "active_predictions": 2,
  "nodes": {
    "node-id-1": {
      "data_points": 95,
      "data_age_seconds": 3.2,
      "model_exists": true,
      "model_age_seconds": 45.8,
      "last_training_duration_ms": 1250,
      "metrics": {
        "r2_score": 0.87,
        "mae": 4.2,
        "rmse": 5.8,
        "samples": 85,
        "trained_at": "2025-11-11T10:25:00"
      },
      "ready_for_training": true,
      "needs_retraining": false
    },
    "node-id-2": {
      "data_points": 25,
      "data_age_seconds": 2.1,
      "model_exists": false,
      "model_age_seconds": null,
      "ready_for_training": false,
      "needs_retraining": true
    }
  }
}
```

---

### Test 8.2: Monitor Data Staleness

```bash
# Check after stopping node (simulate network issue)
docker stop node-<container-id>

# Wait 30 seconds, then check
curl http://localhost:5001/monitoring/stats
```

**Expected:** 
- `data_age_seconds` > 30
- Node marked as needing attention

---

## 9️⃣ Integration Tests

### Test 9.1: Complete Workflow

```bash
# 1. Add nodes
curl -X POST http://localhost:5001/nodes \
  -H "Content-Type: application/json" \
  -d '{"cpu_capacity": 4}'

curl -X POST http://localhost:5001/nodes \
  -H "Content-Type: application/json" \
  -d '{"cpu_capacity": 4}'

# 2