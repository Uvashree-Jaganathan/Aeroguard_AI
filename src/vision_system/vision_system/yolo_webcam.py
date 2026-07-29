import cv2
from ultralytics import YOLO
import rclpy
from rclpy.node import Node
from std_msgs.msg import String

class VisionSafetyNode(Node):
    def __init__(self):
        super().__init__('vision_safety_node')
        self.publisher_ = self.create_publisher(String, 'vision_safety_status', 10)
        
        # Load the YOLOv8 model
        self.model = YOLO('yolov8n.pt')

        # Open the webcam
        self.cap = cv2.VideoCapture(0)

        if not self.cap.isOpened():
            self.get_logger().error("Could not open webcam.")
            return

        # Get webcam resolution to define the Danger Zone (ROI)
        self.frame_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.frame_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        # Define Danger Zone: Center 50% of the screen
        self.roi_x1, self.roi_y1 = int(self.frame_width * 0.25), int(self.frame_height * 0.25)
        self.roi_x2, self.roi_y2 = int(self.frame_width * 0.75), int(self.frame_height * 0.75)

        self.get_logger().info("Vision Safety Node started... Press 'q' to quit.")

    def run(self):
        while rclpy.ok():
            success, frame = self.cap.read()

            if not success:
                self.get_logger().error("Failed to read frame from webcam.")
                break

            results = self.model(frame, stream=True)
            current_overall_status = "SAFE"

            for r in results:
                # Draw the Danger Zone (ROI) on the frame
                cv2.rectangle(frame, (self.roi_x1, self.roi_y1), (self.roi_x2, self.roi_y2), (255, 255, 255), 1)
                cv2.putText(frame, "DANGER ZONE", (self.roi_x1, self.roi_y1 - 10), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

                boxes = r.boxes
                for box in boxes:
                    x1, y1, x2, y2 = box.xyxy[0]
                    width = x2 - x1
                    height = y2 - y1
                    area = width * height
                    
                    center_x = (x1 + x2) / 2
                    center_y = (y1 + y2) / 2
                    is_in_roi = self.roi_x1 < center_x < self.roi_x2 and self.roi_y1 < center_y < self.roi_y2
                    
                    if area > 100000 and is_in_roi:
                        status = "CRITICAL"
                        color = (0, 0, 255)
                    elif area > 40000 or is_in_roi:
                        status = "WARNING"
                        color = (0, 255, 255)
                    else:
                        status = "SAFE"
                        color = (0, 255, 0)
                    
                    if status == "CRITICAL":
                        current_overall_status = "CRITICAL"
                    elif status == "WARNING" and current_overall_status != "CRITICAL":
                        current_overall_status = "WARNING"
                    
                    cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), color, 2)
                    cv2.putText(frame, status, (int(x1), int(y1) - 10), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)

            msg = String()
            msg.data = current_overall_status
            self.publisher_.publish(msg)

            cv2.imshow('Drone Vision - ROS 2 Node', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        self.cap.release()
        cv2.destroyAllWindows()

def main():
    rclpy.init()
    node = VisionSafetyNode()
    try:
        node.run()
    except KeyboardInterrupt:
        pass
    finally:
        rclpy.shutdown()

if __name__ == "__main__":
    main()
