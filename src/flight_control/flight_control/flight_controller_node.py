import rclpy
from rclpy.node import Node
from std_msgs.msg import String

class FlightControllerNode(Node):
    def __init__(self):
        super().__init__('flight_controller_node')
        
        # Current state of the drone
        self.drone_state = "IDLE"
        
        # Subscriber to the final safety command from the Fusion Node
        self.command_sub = self.create_subscription(
            String,
            '/drone_final_command',
            self.command_callback,
            10
        )
        
        self.get_logger().info("Flight Controller Node initialized. Waiting for safety commands...")

    def command_callback(self, msg):
        command = msg.data
        
        # Logic to transition drone states based on the command
        if "HOVER IN PLACE" in command:
            self.execute_action("EMERGENCY_HOVER")
        elif "RETURN TO HOME" in command:
            self.execute_action("RTH")
        elif "CAUTION MODE" in command or "Reduced Speed" in command:
            self.execute_action("CAUTIOUS_FLIGHT")
        elif "NORMAL OPERATION" in command:
            self.execute_action("MISSION_FLIGHT")
        else:
            self.get_logger().warn(f"Received unknown command: {command}")

    def execute_action(self, action):
        if self.drone_state == action:
            # Already in this state, no need to log repeatedly
            return

        self.drone_state = action
        
        # Simulate the physical reaction of the drone
        if action == "EMERGENCY_HOVER":
            self.get_logger().error("🛑 [ACTUATOR] STOPPING ALL MOTORS -> ENTERING EMERGENCY HOVER")
        elif action == "RTH":
            self.get_logger().warn("🏠 [ACTUATOR] ENGAGING GPS RETURN-TO-HOME SEQUENCE")
        elif action == "CAUTIOUS_FLIGHT":
            self.get_logger().info("🐢 [ACTUATOR] LIMITING MAX SPEED TO 2m/s")
        elif action == "MISSION_FLIGHT":
            self.get_logger().info("🚀 [ACTUATOR] RESUMING NORMAL MISSION PARAMETERS")

def main(args=None):
    rclpy.init(args=args)
    node = FlightControllerNode()
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
