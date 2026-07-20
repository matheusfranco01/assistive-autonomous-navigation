#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
udp_joy_bridge.py

Roda DENTRO do container assistive-navigation-real (rede host).
Recebe pacotes UDP do script Windows (windows_joy_sender.py) com o estado
do joystick Bluetooth, aplica a trava de segurança (dead-man's switch:
só publica movimento enquanto o botão de "enable" estiver pressionado),
e publica geometry_msgs/Twist em /RosAria/cmd_vel.

Inclui watchdog: se nenhum pacote chegar por WATCHDOG_TIMEOUT segundos
(ex: Windows travou, Bluetooth caiu), zera o cmd_vel automaticamente -
o robô não fica andando "preso" num último comando.

Uso:
    rosrun p3dx_mapping udp_joy_bridge.py
    (ou direto: python3 udp_joy_bridge.py, com o ambiente ROS já sourced)
"""

import json
import socket
import threading
import time

import rospy
from geometry_msgs.msg import Twist

UDP_IP = "0.0.0.0"
UDP_PORT = 5005
WATCHDOG_TIMEOUT = 0.5  # segundos sem pacote -> para o robô

# Mesma filosofia de escala do joystick.yaml
SCALE_LINEAR = 0.5
SCALE_ANGULAR = 1.0


class UdpJoyBridge:
    def __init__(self):
        rospy.init_node('udp_joy_bridge')

        self.cmd_pub = rospy.Publisher('/RosAria/cmd_vel', Twist, queue_size=1)

        self.lock = threading.Lock()
        self.last_packet_time = 0.0
        self.linear = 0.0
        self.angular = 0.0
        self.enabled = False

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((UDP_IP, UDP_PORT))
        self.sock.settimeout(1.0)

        self.listener_thread = threading.Thread(target=self._listen_loop, daemon=True)
        self.listener_thread.start()

        rospy.loginfo('udp_joy_bridge: ouvindo UDP em %s:%d, publicando em /RosAria/cmd_vel', UDP_IP, UDP_PORT)

        self.rate = rospy.Rate(20)  # 20 Hz de publicação/watchdog

    def _listen_loop(self):
        while not rospy.is_shutdown():
            try:
                data, addr = self.sock.recvfrom(1024)
            except socket.timeout:
                continue
            except OSError:
                break

            try:
                packet = json.loads(data.decode('utf-8'))
                with self.lock:
                    self.linear = float(packet.get('linear', 0.0))
                    self.angular = float(packet.get('angular', 0.0))
                    self.enabled = bool(packet.get('enabled', False))
                    self.last_packet_time = time.time()
            except (ValueError, KeyError, UnicodeDecodeError) as e:
                rospy.logwarn_throttle(5, 'udp_joy_bridge: pacote inválido recebido: %s', e)

    def run(self):
        while not rospy.is_shutdown():
            with self.lock:
                age = time.time() - self.last_packet_time
                linear = self.linear
                angular = self.angular
                enabled = self.enabled

            twist = Twist()

            # Watchdog: sem pacote recente -> robô para, não importa o resto
            if age > WATCHDOG_TIMEOUT:
                enabled = False

            # Trava de segurança: só move com o botão (L1/LB) pressionado
            if enabled:
                twist.linear.x = linear * SCALE_LINEAR
                twist.angular.z = angular * SCALE_ANGULAR
            # else: twist fica zerado (Twist() já inicializa tudo em 0.0)

            self.cmd_pub.publish(twist)
            self.rate.sleep()


if __name__ == '__main__':
    try:
        bridge = UdpJoyBridge()
        bridge.run()
    except rospy.ROSInterruptException:
        pass
