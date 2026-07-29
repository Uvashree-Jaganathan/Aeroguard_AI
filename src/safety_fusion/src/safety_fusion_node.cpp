#include <chrono>
#include <functional>
#include <memory>
#include <string>
#include <iostream>
#include "rclcpp/rclcpp.hpp"
#include "std_msgs/msg/string.hpp"

using namespace std::chrono_literals;

class SafetyFusionNode : public rclcpp::Node {
public:
    SafetyFusionNode() : Node("safety_fusion_node") {
        vision_status_ = "SAFE";
        network_status_ = "SAFE";
        
        // Heartbeat timestamps
        start_time_ = this->now();
        last_vision_time_ = this->now();
        last_network_time_ = this->now();
        timeout_limit_ = 10.0; // 10 seconds for CRITICAL
        stale_limit_ = 2.0;    // 2 seconds for STALE/WARNING
        startup_grace_period_ = 15.0; // Ignore timeouts for first 15 seconds

        vision_sub_ = this->create_subscription<std_msgs::msg::String>(
            "drone/safety_status", 10, 
            std::bind(&SafetyFusionNode::vision_callback, this, std::placeholders::_1));
        
        network_sub_ = this->create_subscription<std_msgs::msg::String>(
            "/network_safety_status", 10, 
            std::bind(&SafetyFusionNode::network_callback, this, std::placeholders::_1));
        
        command_pub_ = this->create_publisher<std_msgs::msg::String>("/drone_final_command", 10);

        timer_ = this->create_wall_timer(
            200ms, std::bind(&SafetyFusionNode::fusion_logic_callback, this));

        RCLCPP_INFO(this->get_logger(), "C++ Safety Fusion Node started with Heartbeat Monitoring...");
    }

private:
    void vision_callback(const std_msgs::msg::String::SharedPtr msg) {
        vision_status_ = msg->data;
        last_vision_time_ = this->now();
    }

    void network_callback(const std_msgs::msg::String::SharedPtr msg) {
        network_status_ = msg->data;
        last_network_time_ = this->now();
    }

    void fusion_logic_callback() {
        rclcpp::Time now = this->now();
        double time_since_start = (now - start_time_).seconds();
        
        // --- HEARTBEAT CHECK ---
        std::string current_vision = vision_status_;
        double vision_diff = (now - last_vision_time_).seconds();
        if (time_since_start > startup_grace_period_) {
            if (vision_diff > timeout_limit_) {
                current_vision = "CRITICAL";
            } else if (vision_diff > stale_limit_) {
                current_vision = "WARNING"; // Mark as warning if data is stale
            }
        }

        std::string current_network = network_status_;
        double network_diff = (now - last_network_time_).seconds();
        if (time_since_start > startup_grace_period_) {
            if (network_diff > timeout_limit_) {
                current_network = "CRITICAL";
            } else if (network_diff > stale_limit_) {
                current_network = "WARNING"; // Mark as warning if data is stale
            }
        }
        
        std::string final_command;
        std::string color = "\033[92m"; // Green

        // 1. Highest Priority: Vision Critical -> HOVER
        if (current_vision == "CRITICAL") {
            final_command = "🚨 HOVER IN PLACE (Obstacle Critical or Blind!)";
            color = "\033[91m"; // Red
        }
        // 2. Second Priority: Network Critical -> RETURN TO HOME
        else if (current_network == "CRITICAL") {
            final_command = "🏠 AUTO-RETURN TO HOME (Connection Lost!)";
            color = "\033[91m"; // Red
        }
        // 3. Third Priority: Both Warning -> CAUTION MODE
        else if (current_vision == "WARNING" && current_network == "WARNING") {
            final_command = "⚠️ CAUTION MODE (Unstable Link & Obstacles)";
            color = "\033[93m"; // Yellow
        }
        // 4. General Warning
        else if (current_vision == "WARNING" || current_network == "WARNING") {
            final_command = "⚠️ WARNING: Reduced Speed";
            color = "\033[93m"; // Yellow
        }
        else {
            final_command = "✅ NORMAL OPERATION";
            color = "\033[92m"; // Green
        }

        // Publish the final command
        auto msg = std_msgs::msg::String();
        msg.data = final_command;
        command_pub_->publish(msg);

        RCLCPP_INFO(this->get_logger(), "%s[Vision: %s | Network: %s] -> DECISION: %s\033[0m", 
                    color.c_str(), current_vision.c_str(), current_network.c_str(), final_command.c_str());
    }

    rclcpp::Time start_time_;
    std::string vision_status_;
    std::string network_status_;
    rclcpp::Time last_vision_time_;
    rclcpp::Time last_network_time_;
    double timeout_limit_;
    double stale_limit_;
    double startup_grace_period_;

    rclcpp::Subscription<std_msgs::msg::String>::SharedPtr vision_sub_;
    rclcpp::Subscription<std_msgs::msg::String>::SharedPtr network_sub_;
    rclcpp::Publisher<std_msgs::msg::String>::SharedPtr command_pub_;
    rclcpp::TimerBase::SharedPtr timer_;
};

int main(int argc, char * argv[]) {
    rclcpp::init(argc, argv);
    rclcpp::spin(std::make_shared<SafetyFusionNode>());
    rclcpp::shutdown();
    return 0;
}
