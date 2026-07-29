import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import time

class NetworkSimulatorNode(Node):
    def __init__(self):
        super().__init__('network_simulator_node')
        self.publisher_ = self.create_publisher(String, '/network_safety_status', 10)
    
        # Format: (duration_seconds, status)
        self.scenario = [
            (10, "SAFE"),      # Starting: Everything is fine
            (10, "WARNING"),   # Entering a tunnel: Signal becomes unstable
            (10, "CRITICAL"),  # Deep tunnel: Connection lost
            (10, "WARNING"),   # Exiting tunnel: Signal returning
            (10, "SAFE"),      # Back in open area: Stable again
        ]
    
        self.current_step = 0
        self.step_start_time = time.time()
        
        self.timer = self.create_timer(0.5, self.timer_callback)
        
        self.get_logger().info("Network Simulator started. Simulating 'Train Journey' scenario...")

    def timer_callback(self):
        now = time.time()
        duration, status = self.scenario[self.current_step]
        
        msg = String()
        msg.data = status
        self.publisher_.publish(msg)
        
        # Check if it's time to move to the next state in the scenario
        if (now - self.step_start_time) > duration:
            self.current_step += 1
            self.step_start_time = now
            
            if self.current_step >= len(self.scenario):
                self.get_logger().info("Scenario complete. Resetting to start...")
                self.current_step = 0
            
            new_status = self.scenario[self.current_step][1]
            self.get_logger().info(f"Transitioning network state to: {new_status}")

def main(args=None):
    rclpy.init(args=args)
    node = NetworkSimulatorNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
