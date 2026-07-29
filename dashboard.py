import streamlit as st
import json
import time
import pandas as pd
from datetime import datetime
import threading
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float64MultiArray, String

# Page configuration
st.set_page_config(
    page_title="Drone Network Safety Dashboard",
    page_icon="🛸",
    layout="wide"
)

st.title("🛸 Drone Network Safety Monitor")
st.markdown("Real-time LSTM-based Network Prediction & Safety Status")

# Sidebar for system info
st.sidebar.header("System Status")
st.sidebar.info("Monitoring: LSTM Prediction Engine & Safety Fusion Node")

# ROS 2 Subscriber Class
class NetworkSubscriber(Node):
    def __init__(self):
        super().__init__('dashboard_subscriber')
        self.current_data = None
        self.current_status = "WAITING"
        self.current_vision_status = "WAITING"
        self.current_command = "WAITING"
        self.current_probs = {'SAFE': 0.0, 'WARNING': 0.0, 'CRITICAL': 0.0}
        
        # ROS 2 Subscriptions
        self.create_subscription(Float64MultiArray, '/network_status', self.metrics_callback, 10)
        self.create_subscription(String, '/network_safety_status', self.status_callback, 10)
        self.create_subscription(String, '/drone/safety_status', self.vision_callback, 10)
        self.create_subscription(String, '/drone_final_command', self.command_callback, 10)
        self.create_subscription(String, '/network_probs', self.probs_callback, 10)

    def metrics_callback(self, msg):
        if len(msg.data) >= 3:
            self.current_data = {
                'rssi': msg.data[0],
                'latency': msg.data[1],
                'loss': msg.data[2]
            }

    def status_callback(self, msg):
        self.current_status = msg.data.strip()

    def vision_callback(self, msg):
        self.current_vision_status = msg.data.strip()

    def command_callback(self, msg):
        self.current_command = msg.data.strip().upper()

    def probs_callback(self, msg):
        try:
            self.current_probs = json.loads(msg.data)
        except Exception:
            pass


# -------------------------------------------------------------------
# FIX: Use @st.cache_resource to initialize ROS 2 ONLY ONCE
# -------------------------------------------------------------------
@st.cache_resource
def get_ros_node():
    if not rclpy.ok():
        rclpy.init()
    
    node = NetworkSubscriber()
    
    # Spin in a dedicated background thread
    spin_thread = threading.Thread(target=rclpy.spin, args=(node,), daemon=True)
    spin_thread.start()
    
    return node

# Get single node instance
try:
    ros_node = get_ros_node()
except Exception as e:
    st.error(f"Failed to initialize ROS 2: {e}")
    ros_node = None


# Placeholder container for dynamic UI updates
placeholder = st.empty()

def get_latest_data():
    if ros_node and ros_node.current_data:
        return {
            'status': ros_node.current_status,
            'vision_status': ros_node.current_vision_status,
            'command': ros_node.current_command,
            'rssi': ros_node.current_data['rssi'],
            'latency': ros_node.current_data['latency'],
            'loss': ros_node.current_data['loss'],
            'probs': ros_node.current_probs
        }
    return None

# Streamlit Live Refresh Loop
while True:
    data = get_latest_data()
    
    with placeholder.container():
        if data:
            # SECTION 1: Status Banners
            col_net, col_vis, col_cmd = st.columns(3)
            
            with col_net:
                status = data['status']
                net_color = "#28a745" if status == "SAFE" else "#ffc107" if status == "WARNING" else "#dc3545"
                st.markdown(f"""
                    <div style="text-align: center; padding: 10px; border-radius: 8px; background-color: {net_color}; color: white; font-weight: bold; font-size: 16px;">
                        NETWORK: {status}
                    </div>
                """, unsafe_allow_html=True)
            
            with col_vis:
                v_status = data['vision_status']
                vis_color = "#28a745" if v_status == "SAFE" else "#ffc107" if v_status == "WARNING" else "#dc3545"
                st.markdown(f"""
                    <div style="text-align: center; padding: 10px; border-radius: 8px; background-color: {vis_color}; color: white; font-weight: bold; font-size: 16px;">
                        VISION: {v_status}
                    </div>
                """, unsafe_allow_html=True)

            with col_cmd:
                cmd = data['command']
                if "HOVER" in cmd:
                    cmd_color = "#fd7e14"
                    icon = "🛑"
                    label = "HOVER IN PLACE"
                elif "CRITICAL" in cmd or "EMERGENCY" in cmd or "RETURN" in cmd or "RTH" in cmd:
                    cmd_color = "#dc3545"
                    icon = "🚨"
                    label = f"CRITICAL: {cmd}" if "CRITICAL" not in cmd else cmd
                elif "WARN" in cmd:
                    cmd_color = "#ffc107"
                    icon = "⚠️"
                    label = "WARNING MODE"
                elif "SAFE" in cmd or "NORMAL" in cmd or "CONTINUE" in cmd:
                    cmd_color = "#28a745"
                    icon = "✅"
                    label = "SAFE / NORMAL"
                else:
                    cmd_color = "#6c757d"
                    icon = "ℹ️"
                    label = cmd

                st.markdown(f"""
                    <div style="text-align: center; padding: 10px; border-radius: 8px; background-color: {cmd_color}; color: white; font-weight: bold; font-size: 16px;">
                        COMMAND: {icon} {label}
                    </div>
                """, unsafe_allow_html=True)
            
            st.markdown("---")
            
            # SECTION 2: Real-time Telemetry
            col1, col2, col3 = st.columns(3)
            col1.metric("RSSI Signal", f"{data['rssi']:.2f} dBm")
            col2.metric("Network Latency", f"{data['latency']:.2f} ms")
            col3.metric("Packet Loss", f"{data['loss']:.2f}%")
            
            st.markdown("### 🧠 LSTM Prediction Engine Probabilities")
            
            # SECTION 3: Class Probabilities
            probs = data['probs']
            predicted_state = max(probs, key=probs.get) if probs else "SAFE"
            prob_value = probs.get(predicted_state, 0.0) * 100
            
            st.info(f"🔮 **Prediction:** Network likely to be **{predicted_state}** in the next 5 seconds ({prob_value:.1f}% confidence).")
            
            p_col1, p_col2, p_col3 = st.columns(3)
            with p_col1:
                st.markdown(f"**🟢 SAFE**\n\n## {probs.get('SAFE', 0.0)*100:.1f}%")
            with p_col2:
                st.markdown(f"**🟡 WARNING**\n\n## {probs.get('WARNING', 0.0)*100:.1f}%")
            with p_col3:
                st.markdown(f"**🔴 CRITICAL**\n\n## {probs.get('CRITICAL', 0.0)*100:.1f}%")
            
            # SECTION 4: Timestamp Footer
            st.caption(f"Last updated: {datetime.now().strftime('%H:%M:%S')}")
            
        else:
            st.warning("⏳ Waiting for data from ROS 2 nodes... Please ensure your launch file is running.")

    time.sleep(0.5)
