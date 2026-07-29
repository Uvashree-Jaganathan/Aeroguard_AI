#  AeroGuard AI: Autonomous Drone Safety System

AeroGuard AI is a sophisticated ROS 2-based safety layer designed to protect autonomous drones by fusing real-time computer vision and network telemetry. The system monitors for physical obstacles and communication instability, automatically overriding flight commands to ensure drone safety.

##  Core Functionality

The system operates as a safety "brain" that continuously evaluates the environment and connection quality to make critical flight decisions:

###  Vision Safety (YOLOv8)
- **Real-time Detection:** Uses a YOLOv8 model to detect objects via a webcam.
- **Danger Zone Monitoring:** Implements a Region of Interest (ROI) in the center of the frame.
- **Dynamic Severity:** 
  - `CRITICAL`: Large objects within the Danger Zone.
  - `WARNING`: Medium objects or objects entering the ROI.
  - `SAFE`: No immediate threats.

### Network Intelligence (LSTM)
- **Telemetry Tracking:** Monitors RSSI (Signal Level), Latency, and Packet Loss.
- **Predictive Analysis:** Uses a trained LSTM (Long Short-Term Memory) neural network to predict network instability before it leads to a total disconnect.
- **Status Output:** Publishes `SAFE`, `WARNING`, or `CRITICAL` based on ML predictions.

### Safety Fusion Logic
The Fusion Node acts as the final decision-maker, prioritizing safety based on the following hierarchy:
1. **Vision Critical** $\rightarrow$ 🚨 **EMERGENCY HOVER** (Immediate obstacle threat or blindness).
2. **Network Critical** $\rightarrow$ 🏠 **AUTO-RETURN TO HOME** (Loss of command link).
3. **Combined Warning** $\rightarrow$ ⚠️ **CAUTION MODE** (Unstable link + obstacles).
4. **General Warning** $\rightarrow$ ⚠️ **REDUCED SPEED** (Minor instability or distant obstacles).
5. **All Clear** $\rightarrow$ ✅ **NORMAL OPERATION**.

###  Flight Control Execution
The Flight Controller simulates the drone's physical response to the fusion commands, transitioning between states like `EMERGENCY_HOVER`, `RTH`, `CAUTIOUS_FLIGHT`, and `MISSION_FLIGHT`.

---

##  System Architecture

### High-Level Topic Flow
`Vision Node` $\rightarrow$ `/vision_safety_status` $\searrow$
$\quad \quad \quad \quad \quad \quad \quad \quad \quad \quad \quad \quad \quad \quad \quad \quad \quad \quad \quad \quad \quad$ **`Safety Fusion Node`** $\rightarrow$ `/drone_final_command` $\rightarrow$ **`Flight Controller`**
`Network Node` $\rightarrow$ `/network_safety_status` $\nearrow$

### Component Breakdown
* **`vision_system`**: YOLOv8-based obstacle detection.
* **`network_system`**: LSTM-based network health prediction.
* **`safety_fusion`**: Decision logic and heartbeat monitoring.
* **`flight_control`**: Actuator simulation and state management.
* **`dashboard.py`**: Streamlit UI for live monitoring of probabilities and safety states.

## Dependencies

This project requires:
* **ROS 2 Jazzy**
* **Python 3.12**
* **ML/Vision:** `tensorflow`, `ultralytics`, `opencv-python`, `scikit-learn`
* **UI/Data:** `streamlit`, `pandas`, `numpy`, `joblib`

### Setup Instructions

1. **Environment Setup:**
```bash
cd ~/Aeroguard_AI
python3 -m venv venv
source venv/bin/activate
python -m pip install --upgrade pip
python -m pip install streamlit tensorflow numpy pandas scikit-learn opencv-python ultralytics joblib
```

2. **ROS 2 Configuration:**
```bash
source /opt/ros/jazzy/setup.bash
colcon build
source install/setup.bash
```

## 🏃 Running the System

### Launch All Nodes
```bash
ros2 launch safety_fusion start_all.launch.py
```

### Launch Dashboard
```bash
streamlit run dashboard.py
```
source install/setup.bash
ros2 launch safety_fusion start_all.launch.py
```

### Dashboard
Run the Streamlit dashboard in a separate terminal:

```bash
cd ~/Aeroguard_AI
source /opt/ros/jazzy/setup.bash
source ~/Aeroguard_AI/venv/bin/activate
python -m streamlit run dashboard.py
```

If you need to run nodes individually for debugging, use the Python scripts directly.

## Training the LSTM model

If you want to regenerate the LSTM model:

```bash
cd ~/Aeroguard_AI
source /opt/ros/jazzy/setup.bash
source ~/Aeroguard_AI/venv/bin/activate
python3 prepare_lstm_data.py
python3 train_network_model.py
```

This creates:
* `X_train_lstm.npy`
* `X_test_lstm.npy`
* `y_train_lstm.npy`
* `y_test_lstm.npy`
* `lstm_scaler.joblib`
* `network_model.h5`

## Files of interest

* `dashboard.py` — Streamlit dashboard client.
* `yolo_webcam.py` — Vision safety ROS node using YOLOv8.
* `network_monitor_node.py` — Network health ROS node with LSTM prediction.
* `safety_fusion_node.py` — Fusion logic node.
* `flight_controller_node.py` — Simulated flight controller node.
* `network_simulator_node.py` — Optional test simulator.
* `safety_logger_node.py` — Safety audit logger.
* `network_logger_node.py` — Network telemetry logger.
* `start_all.launch.py` — Multi-node ROS2 launch file.

## Stopping the system

Press `Ctrl + C` in each terminal to stop the running nodes and dashboard.

##  Notes

* The vision node requires a connected webcam.
* `network_monitor_node.py` reads `network_model.h5` and `lstm_scaler.joblib` from the project root.
* The dashboard expects ROS2 topics to be available and requires `streamlit`.
* Use `ros2 topic list` and `ros2 node list` to verify ROS2 connectivity if nodes are not publishing.
# Aeroguard_AI
