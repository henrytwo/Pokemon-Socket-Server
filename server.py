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

class room:
    def __init__(self, code):
        self.code = code
        self.clients = []
        self.game_running = True
        self.shuffled = False

        self.engine_thread = threading.Thread(target=self.engine)
        self.engine_thread.start()

    def engine(self):
        while self.game_running:
            try:
                if not self.can_join() and self.client_ready():
                    self.set_turn()

                    print(self.clients)

                    connections[self.clients[1]].message('Waiting for %s to finish their turn' % connections[self.clients[0]].name)

                    while True:
                        connections[self.clients[0]].make_action()
                        message = connections[self.clients[0]].com_get()
                        connections[self.clients[0]].message("Damn how great")

            except:
                print(traceback.format_exc())

                self.game_running = False
                for c in self.clients:
                    connections[c].in_game = False
                    connections[c].result('Engine Error')

    def set_turn(self):

        if not self.shuffled:
            self.shuffled = True
            random.shuffle(self.clients)

            connections[self.clients[0]].message('&cThe opponent has joined the match!&n&n----------&n%s&nvs&n%s&n----------&n&nStart battle!&n' % (connections[self.clients[0]].name, connections[self.clients[1]].name))
            connections[self.clients[1]].message('&cThe opponent has joined the match!&n&n----------&n%s&nvs&n%s&n----------&n&nStart battle!&n' % (connections[self.clients[1]].name, connections[self.clients[0]].name))

        self.clients.append(self.clients[0])
        del self.clients[0]

    def can_join(self):
        return len(self.clients) < 2

    def join(self, uuid):
        if len(self.clients) < 2:
            self.clients.append(uuid)
            return True
        else:
            return False

    def client_ready(self):
        ready = True
        for c in self.clients:
            if not connections[c].in_game:
                ready = False
                break
        return ready

class attack:
    def __init__(self, attack_data):
        self.name = attack_data[0]
        self.cost = int(attack_data[1])
        self.damage = int(attack_data[2])
        if len(attack_data) > 3:
            self.special = attack_data[3]
        else:
            self.special = None

class pokemon:
    def __init__(self, pokemon_data_processed):
        self.name = pokemon_data_processed[0]
        self.hp = pokemon_data_processed[1]
        self.hptotal = pokemon_data_processed[1]
        self.type = pokemon_data_processed[2]
        self.resistance = pokemon_data_processed[3]
        self.weakness = pokemon_data_processed[4]
        self.numattacks = int(pokemon_data_processed[5])
        self.attacks = self.get_attacks(int(pokemon_data_processed[5]), pokemon_data_processed[6:])
        self.energy = 50
        self.stunned = False
        self.disabled = False

    def get_attacks(self, num_attacks, attack_data):
        attacks = {}
        for num in range(0, num_attacks * 4, 4):
            attacks[attack_data[num]] = attack(attack_data[num : num + 3])
        return attacks

class client:
    def __init__(self, conn, addr, client_id):
        self.name = ''
        self.pokemon_dict = {}
        self.selected_pokemon = ''
        self.client_id = client_id

        self.alive = True
        self.in_game = False

        self.in_queue = Queue()
        self.out_queue = Queue()

        self.conn = conn
        self.addr = addr

        self.com_thread_read = threading.Thread(target=self.com_read, args=(conn,))
        self.com_thread_read.start()

        self.com_thread_write = threading.Thread(target=self.com_write, args=(conn,))
        self.com_thread_write.start()

        self.thread_service = threading.Thread(target=self.service)
        self.thread_service.start()

        print('Creating object for: %s:%i' % (addr[0], addr[1]))

    def gen_code(self):
        return str(uuid.uuid4())[0:8]

    def pokemon_update(self):
        update_data = ''
        for pokemon_name in self.pokemon_dict:
            update_data += ' // %s // %s // %s' % (pokemon_name, self.pokemon_dict[pokemon_name].hp, self.pokemon_dict[pokemon_name].energy)
        return update_data[4:]

    def make_action(self):
        self.out_queue.put('2 // MakeAction // %s' % self.pokemon_update())
        return self.in_queue.get()

    def make_choose(self):
        self.out_queue.put('2 // MakeChoose // %s' % self.pokemon_update())
        return self.in_queue.get()

    def draw(self, m):
        self.out_queue.put('2 // Draw // %s' % m)

    def message(self, m):
        self.out_queue.put('2 // Message // %s' % m)

    def result(self, m):
        self.out_queue.put('2 // Result // %s' % m)
        
    def service(self):
        while self.alive:
            try:
                if not self.in_game:
                    code, message = self.com_get()

                    # Establish communication
                    if code == 3000:
                        self.out_queue.put('3000 // DOCTYPE!')
                        self.name = message[0]

                    # Generate Gamecode
                    elif code == 0:
                        game_code = self.gen_code()
                        rooms[game_code] = room(game_code)
                        self.out_queue.put('0 // %s' % game_code)

                    # Join game
                    elif code == 1:
                        if message[0] in rooms:  # Check if it's valid
                            if rooms[message[0]].can_join():
                                if len(message) == 1 + NUM_POKEMON:
                                    for pokemon_name in message[1:]:
                                        self.pokemon_dict[pokemon_name] = pokemon_data[pokemon_name]

                                    rooms[message[0]].join(self.client_id)
                                    self.out_queue.put('1 // Success: Connected to room')
                                else:
                                    self.out_queue.put('-1 // Error: Invalid Data')
                            else:
                                self.out_queue.put('-1 // Error: Room Full')
                        else:
                            self.out_queue.put('-1 // Error: Invalid Code')

                    # Preparing to enter game loop
                    elif code == 2:
                        if message[0] == 'InitPkmn':
                            self.selected_pokemon = message[1]
                            self.out_queue.put('2 // Success: Pokemon Registered')

                        elif message[0] == 'Ready':
                            self.message('Waiting for opponent to join...')
                            self.in_game = True

            except:
                print(traceback.format_exc())
                self.alive = False
        try:
            print('Client Disconnected')
            conn.send(bytes('-1 // Server Closed\r\n', 'utf-8'))
        except:
            pass

    def com_read(self, conn):
        while self.alive:
            try:
                message_in = bytes.decode(conn.recv(1024), 'utf-8')
                print('In:', message_in)
                self.in_queue.put(message_in)
            except:
                self.alive = False
                print(traceback.format_exc())

    def com_write(self, conn):
        while self.alive:
            try:
                message_out = self.out_queue.get()
                print('Out:', message_out)
                conn.send(bytes(message_out + '\r\n', 'utf-8'))
            except:
                self.alive = False
                print(traceback.format_exc())

    def com_get(self):
        try:
            data_in = self.in_queue.get()

            if data_in.count(' // ') == 0:
                self.result('-1 // Error: Connection Error')
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

def gen_uuid():
    return str(uuid.uuid4())

with open('data/config.rah', 'r') as config:
    config = config.read().strip().split('\n')
    HOST = config[0]  # The ip address that the socket will bind to
    PORT = int(config[1])  # The port that the socket will bind to
    NUM_POKEMON = int(config[2])

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

        pokemon_data[pokemon_data_processed[0]] = pokemon(pokemon_data_processed[0:])

if __name__ == '__main__':

    rooms = {}
    connections = {}

    PORT = random.randint(2000,3000)

    print('STARTING RASTERA POKEMON SERVER')
    print(' | rastera.xyz')
    print(' | SERIES F2017')
    print('\nStarting server: %s:%i' % (HOST, PORT))

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Start TCP server
    server.bind((HOST, PORT))
    server.listen(1000)

    #log_queue = Queue()
    #log_process = Process(target=logger, args=(log_queue,))
    #log_process.start()

    # Creates client object for each incoming connection
    while True:
        try:
            print(connections)
            conn, addr = server.accept()
            client_id = gen_uuid()
            connections[client_id] = client(conn, addr, client_id)
        except:
            pass
