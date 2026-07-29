import rclpy
from rclpy.node import Node
from std_msgs.msg import Float64MultiArray, String
import subprocess
import re
import time
import json
import joblib
import numpy as np
from collections import deque
import tensorflow as tf

class NetworkMonitorNode(Node):
    def __init__(self):
        super().__init__('network_monitor_node')
        
        # Configuration
        self.target_ip = "8.8.8.8"  # Change this to your drone's ground station IP
        self.publish_frequency = 1.0  
        self.window_size = 10  # Must match the window size used in prepare_lstm_data.py
        
        self.data_buffer = deque(maxlen=self.window_size)
        
        # Array format: [rssi, latency, packet_loss]
        self.publisher_ = self.create_publisher(Float64MultiArray, '/network_status', 10)
        
        # Publishes: "SAFE", "WARNING", "CRITICAL"
        self.status_publisher_ = self.create_publisher(String, '/network_safety_status', 10)

        self.probs_publisher_ = self.create_publisher(String, '/network_probs', 10)

        # Load the trained ML model and Scaler
        model_path = '/home/uva/Aeroguard_AI/src/network_system/network_model.h5'
        scaler_path = '/home/uva/Aeroguard_AI/src/network_system/lstm_scaler.joblib'
        try:
            self.model = tf.keras.models.load_model(model_path)
            self.get_logger().info(f"Network LSTM model loaded successfully from {model_path}")
        except Exception as e:
            self.get_logger().error(f"Failed to load network_model.h5: {e}")
            self.model = None

        try:
            self.scaler = joblib.load(scaler_path)
            self.get_logger().info(f"Network LSTM scaler loaded successfully from {scaler_path}")
        except Exception as e:
            self.get_logger().error(f"Failed to load lstm_scaler.joblib: {e}")
            self.scaler = None
        
        # Timer for periodic measurement
        self.timer = self.create_timer(self.publish_frequency, self.timer_callback)
        
        self.get_logger().info(f'Network Monitor Node started. Monitoring target: {self.target_ip}')

    def get_rssi(self):
        for _ in range(3):  # Try up to 3 times to get a valid reading
            try:
                output = subprocess.check_output(['iwconfig'], stderr=subprocess.STDOUT).decode('utf-8')
                match = re.search(r'Signal level=(-?\d+)\s?dBm', output)
                if match:
                    return float(match.group(1))
            except Exception:
                continue
        return -100.0

    def get_ping_metrics(self):
        try:
            cmd = ['ping', '-c', '3', '-W', '1', self.target_ip]
            output = subprocess.check_output(cmd).decode('utf-8')
            
            loss_match = re.search(r'(\d+)%\s+packet loss', output)
            packet_loss = float(loss_match.group(1)) if loss_match else 100.0
            
            latency_match = re.search(r'rtt min/avg/max/mdev = [\d.]+/([\d.]+)', output)
            latency = float(latency_match.group(1)) if latency_match else 999.0
            
            return latency, packet_loss
        except Exception as e:
            self.get_logger().warn(f'Ping failed: {e}')
            return 999.0, 100.0

    def timer_callback(self):
        # 1. Collect Data
        rssi = self.get_rssi()
        latency, loss = self.get_ping_metrics()
        
        # 2. Create ROS 2 Message
        msg = Float64MultiArray()
        msg.data = [rssi, latency, loss]
        
        # 3. Publish raw data
        self.publisher_.publish(msg)
        
        # 4. Update Buffer for LSTM
        self.data_buffer.append([rssi, latency, loss])
        
        # 5. Predict Safety Status using LSTM Model
        if self.model and self.scaler and len(self.data_buffer) == self.window_size:
            try:
                # Convert buffer to numpy array and scale it
                sequence = np.array(self.data_buffer)
                scaled_sequence = self.scaler.transform(sequence)
                
                # Reshape for LSTM: (1, window_size, num_features)
                features = scaled_sequence.reshape(1, self.window_size, 3)
                
                # Predict probabilities
                prediction_probs = self.model.predict(features, verbose=0)[0]
                prediction = np.argmax(prediction_probs)
                
                # Map prediction to status string
                status_map = {0: "SAFE", 1: "WARNING", 2: "CRITICAL"}
                status = status_map.get(prediction, "UNKNOWN")
                
                # Publish the status string
                status_msg = String()
                status_msg.data = status
                self.status_publisher_.publish(status_msg)
                
                # Publish probabilities as JSON for the dashboard graph
                probs_dict = {
                    "SAFE": float(prediction_probs[0]),
                    "WARNING": float(prediction_probs[1]),
                    "CRITICAL": float(prediction_probs[2])
                }
                probs_msg = String()
                probs_msg.data = json.dumps(probs_dict)
                self.probs_publisher_.publish(probs_msg)
                
                # Log the prediction
                self.get_logger().info(f'LSTM Prediction -> Status: {status}')
            except Exception as e:
                self.get_logger().error(f'Prediction error: {e}')
        elif len(self.data_buffer) < self.window_size:
            self.get_logger().info(f'Filling buffer... ({len(self.data_buffer)}/{self.window_size})')
        
        # Log to console for debugging
        self.get_logger().info(
            f'Published Network Status -> RSSI: {rssi}dBm, Latency: {latency}ms, Loss: {loss}%'
        )

def main(args=None):
    rclpy.init(args=args)
    node = NetworkMonitorNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()

if __name__ == '__main__':
    main()
