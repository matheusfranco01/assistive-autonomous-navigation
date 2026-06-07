#!/usr/bin/env python3

import rospy

from beginner_tutorials.msg import Funcionarios


def callback(mensagem):
    print('O nome do funcionario é: ', mensagem.nome, 'idade =', mensagem.idade, 'com o cargo de', mensagem.cargo, 'Altura:', mensagem.altura)

def listener():
    rospy.init_node('aplicacao', anonymous=True)
    rospy.Subscriber('dados_funcionarios',Funcionarios,callback)
    rospy.spin()


if __name__ == '__main__':
    listener()