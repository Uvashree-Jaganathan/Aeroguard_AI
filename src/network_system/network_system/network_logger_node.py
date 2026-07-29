import rclpy
from rclpy.node import Node
from std_msgs.msg import Float64MultiArray, Int32
import csv
import os
from datetime import datetime

class NetworkLoggerNode(Node):
    def __init__(self):
        super().__init__('network_logger_node')
        
        # File configuration
        self.filename = 'network_dataset.csv'
        self.current_label = 0  # Default: Stable
        
        # Create the file and write the header if it doesn't exist
        if not os.path.exists(self.filename):
            with open(self.filename, mode='w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['timestamp', 'rssi', 'latency', 'packet_loss', 'label'])
        
        # Subscriber for network metrics
        self.subscription = self.create_subscription(
            Float64MultiArray, 
            '/network_status', 
            self.listener_callback, 
            10
        )

        # Subscriber to change the label dynamically
        # Send an Int32 to this topic to change the label (0=Stable, 1=Degrading, 2=Failure)
        self.label_subscription = self.create_subscription(
            Int32,
            '/set_network_label',
            self.label_callback,
            10
        )
        
        self.get_logger().info(f'Network Logger Node started. Saving data to {self.filename}')
        self.get_logger().info('To change label, run: ros2 topic pub /set_network_label std_msgs/msg/Int32 "{data: 1}"')

    def label_callback(self, msg):
        self.current_label = msg.data
        self.get_logger().info(f'Label changed to: {self.current_label}')

    def listener_callback(self, msg):
        # Extract data from the array [rssi, latency, loss]
        if len(msg.data) >= 3:
            rssi = msg.data[0]
            latency = msg.data[1]
            loss = msg.data[2]
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Use the dynamically updated label
            label = self.current_label
            
            # Append to CSV
            with open(self.filename, mode='a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([timestamp, rssi, latency, loss, label])
            
            self.get_logger().info(f'Logged: {timestamp} | RSSI: {rssi}, Lat: {latency}, Loss: {loss}, Label: {label}')
        else:
            self.get_logger().warn('Received malformed network status message')

def main(args=None):
    rclpy.init(args=args)
    node = NetworkLoggerNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
