#!/usr/bin/env python3
"""
Teleop com segurança por LiDAR para o Pioneer 3-DX no Gazebo.
Setas do teclado para mover o robô.
Se detectar obstáculo à frente, para o robô imediatamente e bloqueia avanço.
"""

import rospy
import sys
import tty
import termios
import threading
import math
from geometry_msgs.msg import Twist
from sensor_msgs.msg import LaserScan

# ── Configurações ─────────────────────────────────────────────────────────────
VELOCIDADE_LINEAR  = 0.4   # m/s
VELOCIDADE_ANGULAR = 0.8   # rad/s
DISTANCIA_SEGURA   = 1.0   # metros — distância mínima à frente para bloquear
ANGULO_MONITORADO  = 30    # graus para cada lado do centro (total 60°)

# ── Teclas ────────────────────────────────────────────────────────────────────
SETA_CIMA     = '\x1b[A'
SETA_BAIXO    = '\x1b[B'
SETA_DIREITA  = '\x1b[C'
SETA_ESQUERDA = '\x1b[D'
TECLA_ESPACO  = ' '
TECLA_ESC     = '\x1b'

MSG_BOAS_VINDAS = """
╔══════════════════════════════════════════════╗
║         Teleop Seguro — Pioneer 3-DX         ║
╠══════════════════════════════════════════════╣
║  Seta ↑  →  Andar para frente                ║
║  Seta ↓  →  Andar para trás                  ║
║  Seta ←  →  Girar para esquerda              ║
║  Seta →  →  Girar para direita               ║
║  Espaço  →  Parar                            ║
║  ESC     →  Encerrar                         ║
╠══════════════════════════════════════════════╣
║  Proteção ativa: para se obstáculo < {:.1f}m  ║
╚══════════════════════════════════════════════╝
""".format(DISTANCIA_SEGURA)


class TeleopSeguro:

    def __init__(self):
        rospy.init_node('teleop_seguro', anonymous=True)

        self.pub = rospy.Publisher('/RosAria/cmd_vel', Twist, queue_size=1)
        self.sub = rospy.Subscriber('/scan', LaserScan, self.callback_scan)

        self.obstaculo_frente = False
        rospy.loginfo("Nó teleop_seguro iniciado.")

    # ── Callback do LiDAR ─────────────────────────────────────────────────────
    def callback_scan(self, msg):
        """Verifica cone frontal e para o robô imediatamente se detectar perigo."""
        limite_rad = math.radians(ANGULO_MONITORADO)
        perigo = False

        for i, distancia in enumerate(msg.ranges):
            angulo = msg.angle_min + i * msg.angle_increment
            if -limite_rad <= angulo <= limite_rad:
                if 0.01 < distancia < DISTANCIA_SEGURA:
                    perigo = True
                    break

        # Detectou obstáculo agora — para imediatamente
        if perigo and not self.obstaculo_frente:
            self.pub.publish(Twist())  # Twist zerado = parar
            rospy.logwarn("OBSTACULO DETECTADO! Robo parado. Recue ou gire.")

        # Obstáculo sumiu — avisa que caminho está livre
        if not perigo and self.obstaculo_frente:
            rospy.loginfo("Caminho livre.")

        self.obstaculo_frente = perigo

    # ── Publicar velocidade ───────────────────────────────────────────────────
    def mover(self, linear, angular):
        # Bloqueia avanço se há obstáculo à frente
        if self.obstaculo_frente and linear > 0:
            rospy.logwarn_throttle(1.0, "Frente bloqueada — recue ou gire.")
            linear = 0.0

        twist = Twist()
        twist.linear.x  = linear
        twist.angular.z = angular
        self.pub.publish(twist)

    def parar(self):
        self.pub.publish(Twist())

    # ── Leitura de tecla ──────────────────────────────────────────────────────
    def ler_tecla(self):
        fd = sys.stdin.fileno()
        config_antiga = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            ch = sys.stdin.read(1)
            if ch == '\x1b':
                ch2 = sys.stdin.read(1)
                if ch2 == '[':
                    ch3 = sys.stdin.read(1)
                    return '\x1b[' + ch3
                return ch
            return ch
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, config_antiga)

    # ── Loop principal ────────────────────────────────────────────────────────
    def executar(self):
        print(MSG_BOAS_VINDAS)

        try:
            while not rospy.is_shutdown():
                tecla = self.ler_tecla()

                if tecla == SETA_CIMA:
                    self.mover(VELOCIDADE_LINEAR, 0.0)

                elif tecla == SETA_BAIXO:
                    self.mover(-VELOCIDADE_LINEAR, 0.0)

                elif tecla == SETA_ESQUERDA:
                    self.mover(0.0, VELOCIDADE_ANGULAR)

                elif tecla == SETA_DIREITA:
                    self.mover(0.0, -VELOCIDADE_ANGULAR)

                elif tecla == TECLA_ESPACO:
                    self.parar()
                    print("[ PARADO ]")

                elif tecla == TECLA_ESC:
                    print("\nEncerrando...")
                    self.parar()
                    break

        except rospy.ROSInterruptException:
            pass
        finally:
            self.parar()


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == '__main__':
    teleop = TeleopSeguro()
    teleop.executar()