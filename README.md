# Assistive Autonomous Navigation

Autonomous mobile robotics system developed with ROS for assistive navigation, integrating perception, planning, and human-robot interaction.

The system is built on a Pioneer P3DX platform in simulation (Gazebo) and combines SLAM, autonomous navigation, vision-based tracking, and gesture control into a unified robotic framework.

---

## 🎯 Project Objective

Develop a complete assistive robotics system capable of:

- Mapping unknown environments in real time
- Navigating autonomously using learned maps
- Interacting with humans via gestures
- Following a detected person using vision
- Ensuring safe operation with obstacle avoidance

The focus is system integration: making multiple robotics modules work together in real time.

---

## 🤖 Core Capabilities

### 🗺️ SLAM & Mapping
- Real-time 2D/3D mapping using RTAB-Map
- Sensor fusion with LiDAR and RGB-D camera
- Map generation for navigation and localization

---

### 🤖 Autonomous Navigation
- Path planning using global planners (A*)
- Local obstacle avoidance (DWA)
- ROS Navigation Stack integration
- Execution in dynamic simulated environments (Gazebo)

---

### ✋ Human-Robot Interaction (Gesture Control)
- Hand gesture recognition using MediaPipe
- Webcam-based real-time classification
- Gesture-to-command translation via ROS topics
- Safe teleoperation with LiDAR-based collision prevention

---

### 👤 Person Detection & Following
- Real-time human detection using RGB camera
- Autonomous person-following behavior
- Integration with navigation and obstacle avoidance layers

---

## 🧠 System Integration Insight

While each module is functional independently, the main challenge — and contribution — was integrating all components into a single coherent system.

Key engineering challenges included:

- Synchronization of multiple sensor streams
- Coordinate frame transformations (TF tree)
- Latency management between perception and control loops
- Ensuring stability in concurrent ROS nodes

This integration layer is where the system becomes truly autonomous.

---

## 🧩 System Architecture

- `p3dx_mapping/` → SLAM, mapping, and navigation
- `p3dx_control/` → control, teleoperation, safety layer
- `pioneer_p3dx_model/` → robot model (URDF, Gazebo simulation assets)

---

## 🛠️ Tech Stack

- ROS Noetic
- Python
- Gazebo
- RTAB-Map
- OpenCV
- MediaPipe
- Move Base / Navigation Stack
- WSL2 (development environment)

---

## 📍 Simulation Environment

- Fully developed and tested in Gazebo
- Pioneer P3DX mobile robot model
- Sensors: LiDAR + RGB-D camera
- Modular ROS-based architecture

---

## 🚀 Current Status

- [x] SLAM and mapping
- [x] Autonomous navigation
- [x] Gesture-based control
- [x] Person detection and following
- [x] Safety layer (collision avoidance)
- [x] System integration in simulation
- [ ] Real-world deployment on physical robot

---

## 📷 Media (Optional)

Add here:
- Gazebo simulation screenshots
- RTAB-Map generated maps
- RViz visualization
- Gesture control demo videos

---

## 👨‍💻 Author

Developed as part of robotics and autonomous systems research in a university laboratory, focusing on assistive navigation and human-robot interaction.

---

## 🔗 Repository

github.com/matheusfranco01/assistive-autonomous-navigation
