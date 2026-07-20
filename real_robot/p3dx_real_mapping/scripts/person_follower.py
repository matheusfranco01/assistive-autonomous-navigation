#!/usr/bin/env python3
import rospy
from geometry_msgs.msg import Twist
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2
import mediapipe as mp

mp_pose = mp.solutions.pose
bridge = CvBridge()

# Parâmetros de controle
FRAME_WIDTH = 640
FRAME_HEIGHT = 480
CENTER_X = FRAME_WIDTH // 2
DEAD_ZONE = 40
TARGET_Y = 0.55       # quadril alvo (distância ideal)
HIP_Y_MIN = 0.15      # se hip_y < isso, pessoa muito longe (fora do raio)
KP_ANGULAR = 0.004
KP_LINEAR = 1.2
MAX_LINEAR = 0.5
MAX_ANGULAR = 0.6
SEARCH_ANGULAR = 0.3  # velocidade de busca quando perde a pessoa

# Estado
lost_person_time = None
LOST_TIMEOUT = 2.0    # segundos antes de iniciar busca
target_locked = False
target_x = None       # posição X do alvo atual

twist = Twist()
pub = None

def select_target(results):
    """Seleciona a pessoa mais central no frame como alvo."""
    if not results.pose_landmarks:
        return None
    # Com mediapipe single-person, retorna diretamente
    landmarks = results.pose_landmarks.landmark
    nose = landmarks[mp_pose.PoseLandmark.NOSE]
    left_hip = landmarks[mp_pose.PoseLandmark.LEFT_HIP]
    right_hip = landmarks[mp_pose.PoseLandmark.RIGHT_HIP]
    hip_y = (left_hip.y + right_hip.y) / 2.0
    return nose, hip_y

def image_callback(msg):
    global twist, lost_person_time, target_locked, target_x

    frame = bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = pose.process(rgb)

    target = select_target(results)

    if target is not None:
        nose, hip_y = target

        # Verifica raio máximo — se hip_y muito baixo, pessoa está longe demais
        if hip_y < HIP_Y_MIN:
            twist.linear.x = MAX_LINEAR  # vai na máxima para alcançar
            twist.angular.z = 0.0
            rospy.loginfo_throttle(1.0, f"PESSOA MUITO LONGE (hip_y: {hip_y:.2f}) - acelerando")
            pub.publish(twist)
            lost_person_time = None
            return

        # Pessoa encontrada — resetar timer de busca
        lost_person_time = None
        target_locked = True

        person_x = int(nose.x * FRAME_WIDTH)
        offset_x = person_x - CENTER_X

        # Controle angular proporcional
        if abs(offset_x) > DEAD_ZONE:
            twist.angular.z = -KP_ANGULAR * offset_x
            twist.angular.z = max(-MAX_ANGULAR, min(MAX_ANGULAR, twist.angular.z))
        else:
            twist.angular.z = 0.0

        # Controle linear proporcional à distância
        dist_error = TARGET_Y - hip_y
        if abs(dist_error) > 0.04:
            twist.linear.x = KP_LINEAR * dist_error
            twist.linear.x = max(-0.15, min(MAX_LINEAR, twist.linear.x))
        else:
            twist.linear.x = 0.0

        rospy.loginfo_throttle(0.5, f"offset_x: {offset_x} | hip_y: {hip_y:.2f} | linear: {twist.linear.x:.2f} | angular: {twist.angular.z:.2f}")

    else:
        # Pessoa não detectada
        if lost_person_time is None:
            lost_person_time = rospy.Time.now()

        elapsed = (rospy.Time.now() - lost_person_time).to_sec()

        if elapsed < LOST_TIMEOUT:
            # Para e espera brevemente
            twist.linear.x = 0.0
            twist.angular.z = 0.0
            rospy.loginfo_throttle(1.0, f"Pessoa perdida - aguardando ({elapsed:.1f}s)")
        else:
            # Inicia busca girando
            twist.linear.x = 0.0
            twist.angular.z = SEARCH_ANGULAR
            rospy.loginfo_throttle(1.0, "BUSCANDO pessoa...")

    pub.publish(twist)

def main():
    global pub, pose

    rospy.init_node('person_follower')
    pub = rospy.Publisher('/p3dx/cmd_vel', Twist, queue_size=1)
    rospy.Subscriber('/p3dx/camera/rgb/image_raw', Image, image_callback)

    pose = mp_pose.Pose(
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
        model_complexity=0  # mais rápido
    )

    rospy.loginfo("Person follower iniciado")
    rospy.spin()

if __name__ == '__main__':
    main()