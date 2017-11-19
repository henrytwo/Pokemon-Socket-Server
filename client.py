# RASTERA CLIENT TEST
# COPYRIGHT 2017 (C) RASTERA DEVELOPMENT
# rastera.xyz
# DEVELOPED BY HENRY TU

# client.py

import socket, os, sys
from multiprocessing import *

with open("data/config.rah", "r") as config:  # Reading server settings from a file so that the settings can be easily modifiable and is saved
    config = config.read().strip().split("\n")
    host = config[0]  # The ip address that the socket will bind to
    port = int(config[1])  # The port that the socket will bind to


def commandline_in(fn):
    print('Ready for input.')
    sys.stdin = os.fdopen(fn)  # Opens and links this function/process to the main process's input stream because multiprocessing closes the input stream

    while True:
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Start TCP server
        server.connect(('127.0.0.1', port))

        command = "0 // DASD"#input('> ')  # Getting input
        server.send(bytes(command, 'utf-8'))
        print(bytes.decode(server.recv(1024), 'utf-8'))

if __name__ == '__main__':
    fn = sys.stdin.fileno()
    commandline = Process(target=commandline_in, args=(fn,))
    commandline.start()