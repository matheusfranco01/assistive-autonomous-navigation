#!/usr/bin/env python3
import rospy
from geometry_msgs.msg import Twist
import cv2
import mediapipe as mp

mp_hands = mp.solutions.hands

# Landmarks: tip e pip de cada dedo (indicador, medio, anelar, mindinho)
FINGER_TIPS = [8, 12, 16, 20]
FINGER_PIPS = [6, 10, 14, 18]
FINGER_NAMES = ["indicador", "medio", "anelar", "mindinho"]

def get_fingers_state(landmarks):
    """Retorna lista de booleanos: True = dedo esticado"""
    state = []
    for tip, pip in zip(FINGER_TIPS, FINGER_PIPS):
        state.append(landmarks[tip].y < landmarks[pip].y)
    return state

def classify_gesture(fingers):
    indicador, medio, anelar, mindinho = fingers

    if all(fingers):
        return "FRENTE", 0.3, 0.0
    elif not any(fingers):
        return "PARAR", 0.0, 0.0
    elif indicador and not medio and not anelar and not mindinho:
        return "ESQUERDA", 0.0, 0.5
    elif indicador and medio and not anelar and not mindinho:
        return "DIREITA", 0.0, -0.5
    elif mindinho and not indicador and not medio and not anelar:
        return "RE", -0.2, 0.0
    else:
        return "PARAR", 0.0, 0.0

def main():
    rospy.init_node('gesture_control')
    pub = rospy.Publisher('/p3dx/cmd_vel', Twist, queue_size=1)
    rate = rospy.Rate(10)

    hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.5, min_tracking_confidence=0.5)
    cap = cv2.VideoCapture("http://host.docker.internal:5000/video")

    if not cap.isOpened():
        rospy.logerr("Nao foi possivel abrir o stream da webcam")
        return

    rospy.loginfo("Gesture control iniciado")

    while not rospy.is_shutdown():
        ret, frame = cap.read()
        if not ret:
            rospy.logwarn("Falha ao ler frame")
            continue

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(rgb)

        twist = Twist()

        if results.multi_hand_landmarks:
            lm = results.multi_hand_landmarks[0].landmark
            fingers = get_fingers_state(lm)
            gesto, linear, angular = classify_gesture(fingers)
            twist.linear.x = linear
            twist.angular.z = angular
            rospy.loginfo_throttle(0.5, f"{gesto} | dedos: {fingers}")
        else:
            twist.linear.x = 0.0
            twist.angular.z = 0.0

        pub.publish(twist)
        rate.sleep()

if __name__ == '__main__':
    main()