import os
from launch import LaunchDescription
from launch.actions import ExecuteProcess
from launch_ros.actions import Node

def generate_launch_description():
    # Paths to the python scripts
    # We use absolute paths to ensure the venv can find the files and the files can find their models
    vision_node_path = '/home/uva/Aeroguard_AI/src/vision_system/vision_system/yolo_webcam.py'
    network_node_path = '/home/uva/Aeroguard_AI/src/network_system/network_system/network_monitor_node.py'

    return LaunchDescription([
        # 1. Flight Controller (ROS 2 Node)
        Node(
            package='flight_control',
            executable='flight_controller',
            name='flight_controller_node',
            output='screen'
        ),

        # 2. Safety Fusion Node (C++ Node)
        Node(
            package='safety_fusion',
            executable='safety_fusion_node',
            name='safety_fusion_node',
            output='screen'
        ),

        # 3. Network Monitor (Python Script)
        # We use ExecuteProcess to run it via python3 to ensure venv compatibility
        ExecuteProcess(
            cmd=['python3', network_node_path],
            output='screen'
        ),

        # 4. Vision YOLO (Python Script)
        ExecuteProcess(
            cmd=['python3', vision_node_path],
            output='screen'
        ),
    ])
