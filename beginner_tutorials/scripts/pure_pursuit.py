#!/usr/bin/env python3

import rospy
import numpy as np
from geometry_msgs.msg import Twist, PoseStamped
from nav_msgs.msg import Odometry, Path
import tf.transformations as tf

# ---- Parâmetros ----
LOOK_AHEAD = 0.8
VL = 0.3

# ---- Trajetória ondulada pré-definida ----
t = np.linspace(0, 4 * np.pi, 200)
path_x = list(np.linspace(0, 10, 200))
path_y = list(1.5 * np.sin(t))

# ---- Pose do robô ----
robot_x = 0.0
robot_y = 0.0
robot_theta = 0.0

# ---- Estado ----
arrived = False
robot_path_x = []
robot_path_y = []

# ---- Publishers ----
cmd_pub = None
path_pub = None
robot_path_pub = None

def odom_callback(msg):
    global robot_x, robot_y, robot_theta
    robot_x = msg.pose.pose.position.x
    robot_y = msg.pose.pose.position.y
    q = msg.pose.pose.orientation
    _, _, robot_theta = tf.euler_from_quaternion([q.x, q.y, q.z, q.w])

def publish_path():
    path_msg = Path()
    path_msg.header.frame_id = "p3dx_tf/odom"
    path_msg.header.stamp = rospy.Time.now()
    for x, y in zip(path_x, path_y):
        pose = PoseStamped()
        pose.header.frame_id = "p3dx_tf/odom"
        pose.pose.position.x = x
        pose.pose.position.y = y
        path_msg.poses.append(pose)
    path_pub.publish(path_msg)

def publish_robot_path():
    robot_path_x.append(robot_x)
    robot_path_y.append(robot_y)
    path_msg = Path()
    path_msg.header.frame_id = "p3dx_tf/odom"
    path_msg.header.stamp = rospy.Time.now()
    for x, y in zip(robot_path_x, robot_path_y):
        pose = PoseStamped()
        pose.header.frame_id = "p3dx_tf/odom"
        pose.pose.position.x = x
        pose.pose.position.y = y
        path_msg.poses.append(pose)
    robot_path_pub.publish(path_msg)

def closest_point():
    dx = np.array(path_x) - robot_x
    dy = np.array(path_y) - robot_y
    return int(np.argmin(np.hypot(dx, dy)))

def goal_point():
    closest = closest_point()
    look_ahead_index = closest
    while look_ahead_index < len(path_x):
        dx = path_x[look_ahead_index] - robot_x
        dy = path_y[look_ahead_index] - robot_y
        if np.hypot(dx, dy) >= LOOK_AHEAD:
            break
        look_ahead_index += 1
    if look_ahead_index >= len(path_x):
        look_ahead_index = len(path_x) - 1
    return look_ahead_index

def pure_pursuit():
    goal_index = goal_point()
    dx = path_x[goal_index] - robot_x
    dy = path_y[goal_index] - robot_y
    cos_th = np.cos(-robot_theta)
    sin_th = np.sin(-robot_theta)
    local_y = sin_th * dx + cos_th * dy
    curvature = (2.0 * local_y) / (LOOK_AHEAD ** 2)
    return curvature * VL

def main():
    global cmd_pub, path_pub, robot_path_pub, arrived

    rospy.init_node('pure_pursuit')
    rospy.Subscriber('/p3dx/base_pose_ground_truth', Odometry, odom_callback)
    cmd_pub = rospy.Publisher('/p3dx/cmd_vel', Twist, queue_size=10)
    path_pub = rospy.Publisher('/planned_path', Path, queue_size=10)
    robot_path_pub = rospy.Publisher('/robot_path', Path, queue_size=10)

    rate = rospy.Rate(10)
    rospy.loginfo("Pure Pursuit iniciado!")

    while not rospy.is_shutdown():
        publish_path()
        publish_robot_path()

        if not arrived:
            dx = path_x[-1] - robot_x
            dy = path_y[-1] - robot_y
            if np.hypot(dx, dy) < 0.2:
                rospy.loginfo("Chegou ao destino!")
                cmd_pub.publish(Twist())
                arrived = True
            else:
                omega = pure_pursuit()
                cmd = Twist()
                cmd.linear.x = VL
                cmd.angular.z = omega
                cmd_pub.publish(cmd)

        rate.sleep()

if __name__ == '__main__':
    main()
