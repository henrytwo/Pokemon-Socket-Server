# RASTERA SOCKET SERVER FRAMEWORK
# COPYRIGHT 2017 (C) RASTERA DEVELOPMENT
# rastera.xyz
# DEVELOPED BY HENRY TU

# server.py

import os.path, traceback, socket, sys, uuid, pprint
import threading
from queue import *
from multiprocessing import *
import random
from math import *

class attack:
    def __init__(this, attack_data):
        this.name = attack_data[0]
        this.cost = int(attack_data[1])
        this.damage = int(attack_data[2])
        if len(attack_data) > 3:
            this.special = attack_data[3]
        else:
            this.special = None

class pokemon:
    def __init__(this, pokemon_data_processed):
        this.hp = pokemon_data_processed[0]
        this.hptotal = pokemon_data_processed[0]
        this.type = pokemon_data_processed[1]
        this.resistance = pokemon_data_processed[2]
        this.weakness = pokemon_data_processed[3]
        this.numattacks = int(pokemon_data_processed[4])
        this.attacks = this.get_attacks(int(pokemon_data_processed[4]), pokemon_data_processed[5:])
        this.energy = 50
        this.stunned = False
        this.disabled = False

    def get_attacks(this, num_attacks, attack_data):
        attacks = {}
        for num in range(0, num_attacks * 4, 4):
            attacks[attack_data[num]] = attack(attack_data[num : num + 3])
        return attacks

class client:
    def __init__(this, conn, addr):
        this.alive = True
        this.in_game = False

        this.in_queue = Queue()
        this.out_queue = Queue()

        this.conn = conn
        this.addr = addr

        this.com_thread_read = threading.Thread(target=this.com_read, args=(conn,))
        this.com_thread_read.start()

        this.com_thread_write = threading.Thread(target=this.com_write, args=(conn,))
        this.com_thread_write.start()

        this.thread_service = threading.Thread(target=this.service)
        this.thread_service.start()

        print("Creating object for: %s:%i" % (addr[0], addr[1]))

    def gen_code(this):
        return str(uuid.uuid4())[0:8]

    def pokemon_update(this):
        return ""

    def make_action(this):
        this.out_queue.put("2 // MakeAction // %s" % this.pokemon_update())
        return this.in_queue.get()

    def make_choose(this):
        this.out_queue.put("2 // MakeChoose // %s" % this.pokemon_update())
        return this.in_queue.get()

    def result(this, message):
        this.out_queue.put("2 // Result // %s" % message)
        
    def service(this):
        while this.alive:
            try:
                if not this.in_game:
                    code, message = this.com_get()

                    # Establish communication
                    if code == 3000:
                        this.out_queue.put('3000 // DOCTYPE!')

                    # Generate Gamecode
                    elif code == 0:
                        game_code = this.gen_code()
                        rooms[game_code] = {}
                        this.out_queue.put('0 // %s' % game_code)

                    # Join game
                    elif code == 1:
                        if message[0] in rooms:  # Check if it's valid
                            if len(rooms[message[0]]) > 1:
                                this.out_queue.put('-1 // Error: Room Full')
                            else:
                                if len(message) >= 2:

                                    client_id = str(uuid.uuid4())

                                    rooms[message[0]][client_id] = {
                                        'name': message[1],
                                        'selected_pokemon': '',
                                        'pokemon': get_pokemon(message[3:]),
                                        'turn': not rooms[message[0]]
                                    }

                                    this.out_queue.put('1 // Success: Connected to room // %s' % client_id)

                                else:
                                    this.out_queue.put('-1 // Error: Invalid Data')
                        else:
                            this.out_queue.put('-1 // Error: Invalid Code')
            except:
                print(traceback.format_exc())
                this.alive = False
        try:
            conn.send(bytes('-1 // Server Closed\r\n', 'utf-8'))
        except:
            pass

    def com_read(this, conn):
        while this.alive:
            try:
                message_in = bytes.decode(conn.recv(1024), 'utf-8')
                print('In:', message_in)
                this.in_queue.put(message_in)
            except:
                this.alive = False
                print(traceback.format_exc())

    def com_write(this, conn):
        while this.alive:
            try:
                message_out = this.out_queue.get()
                print('Out:', message_out)
                conn.send(bytes(message_out + '\r\n', 'utf-8'))
            except:
                this.alive = False
                print(traceback.format_exc())

    def com_get(this):
        try:
            data_in = this.in_queue.get()

            if data_in.count(' // ') == 0:
                this.result('-1 // Error: Connection Error')
                return -1

            data_list = data_in.strip('\n').split(' // ')
            code = int(data_list[0])

            if len(data_list) == 0:
                message = []
            else:
                message = data_list[1:]

            return [code, message]
        except:
            print(traceback.format_exc())
            return -1

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
            data_file.flush()

with open('data/config.rah', 'r') as config:
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

        pokemon_data[pokemon_data_processed[0]] = pokemon(pokemon_data_processed[1:])

if __name__ == '__main__':

    rooms = {}
    connections = []

    port = random.randint(2000,3000)

    print('STARTING RASTERA POKEMON SERVER')
    print(' | rastera.xyz')
    print(' | SERIES F2017')
    print('\nStarting server: %s:%i' % (host, port))

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Start TCP server
    server.bind((host, port))
    server.listen(1000)

    #log_queue = Queue()
    #log_process = Process(target=logger, args=(log_queue,))
    #log_process.start()

    # Creates client object for each incoming connection
    while True:
        try:
            conn, addr = server.accept()
            connections.append(client(conn, addr))
        except:
            pass
