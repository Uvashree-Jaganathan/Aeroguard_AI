import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import time

class SafetyFusionNode(Node):
    def __init__(self):
        super().__init__('safety_fusion_node')
        
        # State variables
        self.vision_status = "SAFE"
        self.network_status = "SAFE"
        
        # Heartbeat timestamps
        self.last_vision_time = time.time()
        self.last_network_time = time.time()
        self.timeout_limit = 10.0  # Increased to 10 seconds to prevent false CRITICAL triggers from YOLO lag
        
        # Subscribers
        self.vision_sub = self.create_subscription(
            String, 
            'vision_safety_status', 
            self.vision_callback, 
            10)
        
        self.network_sub = self.create_subscription(
            String, 
            '/network_safety_status', 
            self.network_callback, 
            10)
        
        # Publisher for the final drone command
        self.command_pub = self.create_publisher(String, '/drone_final_command', 10)
        
        # Timer to evaluate fusion logic at 5Hz
        self.timer = self.create_timer(0.2, self.fusion_logic_callback)
        
        self.get_logger().info("Safety Fusion Node started with Heartbeat Monitoring...")

    def vision_callback(self, msg):
        self.vision_status = msg.data
        self.last_vision_time = time.time()

    def network_callback(self, msg):
        self.network_status = msg.data
        self.last_network_time = time.time()

    def fusion_logic_callback(self):
        now = time.time()
        
        # --- HEARTBEAT CHECK ---
        # Check if Vision Node is alive
        current_vision = self.vision_status
        if (now - self.last_vision_time) > self.timeout_limit:
            current_vision = "CRITICAL" # Blindness is critical
            
        # Check if Network Node is alive
        current_network = self.network_status
        if (now - self.last_network_time) > self.timeout_limit:
            current_network = "CRITICAL" # Connection loss is critical
        # -----------------------

        final_command = "NORMAL OPERATION"
        severity_color = "\033[92m" # Green

        # 1. Highest Priority: Vision Critical -> HOVER
        if current_vision == "CRITICAL":
            final_command = "🚨 HOVER IN PLACE (Obstacle Critical or Blind!)"
            severity_color = "\033[91m" # Red
        
        # 2. Second Priority: Network Critical -> RETURN TO HOME
        elif current_network == "CRITICAL":
            final_command = "🏠 AUTO-RETURN TO HOME (Connection Lost!)"
            severity_color = "\033[91m" # Red
            
        # 3. Third Priority: Both Warning -> CAUTION MODE
        elif current_vision == "WARNING" and current_network == "WARNING":
            final_command = "⚠️ CAUTION MODE (Unstable Link & Obstacles)"
            severity_color = "\033[93m" # Yellow
            
        # 4. General Warning
        elif current_vision == "WARNING" or current_network == "WARNING":
            final_command = "⚠️ WARNING: Reduced Speed"
            severity_color = "\033[93m" # Yellow
            
        else:
            final_command = "✅ NORMAL OPERATION"
            severity_color = "\033[92m" # Green

        # Publish the final command
        msg = String()
        msg.data = final_command
        self.command_pub.publish(msg)
        
        # ENHANCED LOGGING: Show exactly what the brain is seeing
        log_msg = f"{severity_color}[Vision: {current_vision} | Network: {current_network}] -> DECISION: {final_command}\033[0m"
        self.get_logger().info(log_msg)

def main(args=None):
    rclpy.init(args=args)
    node = SafetyFusionNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
