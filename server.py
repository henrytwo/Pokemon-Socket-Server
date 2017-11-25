# RASTERA SOCKET SERVER FRAMEWORK
# COPYRIGHT 2017 (C) RASTERA DEVELOPMENT
# rastera.xyz
# DEVELOPED BY HENRY TU

# server.py

import os.path, traceback, socket, sys, uuid, pprint
import threading
from multiprocessing import *
from math import *

with open('data/config.rah', 'r') as config:  # Reading server settings from a file so that the settings can be easily modifiable and is saved
    config = config.read().strip().split("\n")
    host = config[0]  # The ip address that the socket will bind to
    port = int(config[1])  # The port that the socket will bind to

with open('data/pokemon_data.txt', 'r') as file:
    pokemon_data_raw = file.read().strip().split('\n')
    pokemon_data = {}

    # Converts data from string to dictionary
    for line in range(len(pokemon_data_raw)):
        pokemon_data_processed = pokemon_data_raw[line].split(',')

        # Tries to convert all string to int
        for item in range(len(pokemon_data_processed)):
            try:
                pokemon_data_processed[item] = int(pokemon_data_processed[item])
            except:
                pass

        pokemon_data[pokemon_data_processed[0]] = pokemon_data_processed[1:]

# Function to generate game codes
def gen_code():
    return str(uuid.uuid4())[0:8]

# Get the stats of all pokemon
# Gives the player a copy
def get_pokemon(pokemon_list):

    stat_dict = {}

    for pokemon_name in pokemon_list:
        if pokemon_name in pokemon_data:
            stat_dict[pokemon_name] = pokemon_data[pokemon_name]

    return stat_dict

# A function used to write the server log to a file to help with server debugging
def logger(log_queue):
    with open('data/log.log', 'a+') as data_file:
        while True:
            data_file.write(str(log_queue.get()) + '\n')
            data_file.flush()  # Flushing the data so it can be written to the os write queue and be written to the file without calling close

# Allows command line input from server console without stopping the server
def commandline_in(fn):
    print('Ready for input.')
    sys.stdin = os.fdopen(fn)  # Opens and links this function/process to the main process's input stream because multiprocessing closes the input stream

    while True:
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Start TCP server
        server.connect(('127.0.0.1', port))

        command = input('> ')  # Getting input
        server.send(bytes(command, 'utf-8'))
        print("Console: ", bytes.decode(server.recv(1024), 'utf-8'))

        server.close()

def server_process(conn, addr):

    while True:
        try:
            data_in = bytes.decode(conn.recv(1024), 'utf-8')

            print('Connection from: %s:%i' % (addr[0], addr[1]))
            print('Data: %s' % data_in)

            if data_in.count(' // ') == 0:
                conn.send(bytes('-1 // Error: Connection Error\r', 'utf-8'))
                continue

            log_queue.put(data_in)

            data_list = data_in.strip('\n').split(' // ')
            code = int(data_list[0])

            if len(data_list) == 0:
                message = []
            else:
                message = data_list[1:]

            print(code, message, addr)

            if code == 0:  # Generate game code
                game_code = gen_code()
                rooms[game_code] = {}
                conn.send(bytes('0 // %s\r\n' % game_code, 'utf-8'))

            elif code == 1:  # Join game
                if message[0] in rooms:  # Check if it's valid
                    if len(rooms[message[0]]) > 1:
                        conn.send(bytes('1 // Error: Room Full\r\n', 'utf-8'))

                    else:
                        if len(message) >= 2:

                            client_id = str(uuid.uuid4())

                            rooms[message[0]][client_id] = {
                                'name': message[1],
                                'pokemon': get_pokemon(message[2:]),
                                'turn': not rooms[message[0]]
                            }

                            conn.send(bytes('1 // Success: Connected to room // %s\r\n' % client_id, 'utf-8'))

                        else:
                            conn.send(bytes('-1 // Error: Invalid Data\r\n', 'utf-8'))
                else:
                    conn.send(bytes('-1 // Error: Invalid Code\r\n', 'utf-8'))

            elif code == 2:
                if message[0] in rooms and message[1] in rooms[message[0]]:
                    if rooms[message[0]][message[1]]['turn']:
                        pass
                        # When player makes a move

                    else:
                        conn.send(bytes('-1 // Error: Unauthorized - Not your turn\r\n', 'utf-8'))
                else:
                    conn.send(bytes('-1 // Error: Unauthorized - Account not registered\r\n', 'utf-8'))
            else:
                conn.send(bytes('-1 // Error: Connection Error\r\n', 'utf-8'))

        except:

            # Requests for client to be disconnected
            # If client is still connected
            try:
                conn.send(bytes('-1 // Error: Server Error\r\n', 'utf-8'))
            except:
                pass

            conn.close()
            print(traceback.format_exc())  # Crash, print crash message
            return False

def game_process():

    while True:
        pass
        #print(threading.active_count())

if __name__ == '__main__':

    rooms = {}

    print('STARTING RASTERA POKEMON SERVER')
    print(' | rastera.xyz')
    print(' | SERIES F2017')
    print('\nStarting server: %s:%i' % (host, port))

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Start TCP server
    server.bind((host, port))
    server.listen(1000)

    log_queue = Queue()

    log_process = Process(target=logger, args=(log_queue,))
    log_process.start()

    #fn = sys.stdin.fileno()
    #commandline = Process(target=commandline_in, args=(fn,))
    #commandline.start()

    game = threading.Thread(target=game_process, args=())
    game.start()

    # Creates thread for each incoming connection
    while True:
        try:
            conn, addr = server.accept()
            threading.Thread(target=server_process, args=(conn, addr)).start()
        except:
            pass
