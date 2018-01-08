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
from copy import *
import time
from math import *

class room:
    def __init__(self, code):
        self.code = code
        self.clients = []
        self.game_running = True
        self.shuffled = False
        self.death_time = int(time.time() + 3600)

        self.engine_thread = threading.Thread(target=self.engine)
        self.engine_thread.start()

    def engine(self):
        while self.game_running:
            try:
                if int(time.time()) >= self.death_time:
                    self.game_running = False

                if not self.can_join() and self.client_ready():

                    self.death_time = int(time.time() + 3600)
                    self.set_turn()

                    print(self.clients)

                    connections[self.clients[1]].message('Waiting for %s to finish their turn' % connections[self.clients[0]].name)

                    broadcast_turn = False

                    while True:

                        if not broadcast_turn:
                            for c in self.clients:
                                connections[c].message("----- %s's TURN! -----" % connections[self.clients[0]].name)
                            broadcast_turn = True

                        if connections[self.clients[0]].pokemon_dict[connections[self.clients[0]].selected_pokemon].hp <= 0:

                            if len(connections[self.clients[0]].pokemon_dict) == 1:
                                connections[self.clients[0]].result('YOU LOSE!')
                                connections[self.clients[1]].result('YOU WIN!')
                                self.game_running = False

                            connections[self.clients[0]].message("Your Pokemon has fainted! You must pick a replacement to continue fighting!")
                            action = connections[self.clients[0]].make_choose()[1]

                            del connections[self.clients[0]].pokemon_dict[connections[self.clients[0]].selected_pokemon]

                        elif connections[self.clients[0]].pokemon_dict[connections[self.clients[0]].selected_pokemon].stunned:
                            connections[self.clients[0]].pokemon_dict[connections[self.clients[0]].selected_pokemon].stunned = False

                            for c in self.clients:
                                connections[self.clients[c]].message("%s IS STUNNED!" % connections[self.clients[0]].pokemon_dict[connections[self.clients[0]].selected_pokemon].name)

                            action = ['Pass']

                        else:
                            action = connections[self.clients[0]].make_action()[1][0:]

                        print(action)

                        if action:
                            if action[0] == 'Pass':
                                for c in self.clients:
                                    connections[c].message("%s passed their turn&n" % connections[self.clients[0]].name)

                                break

                            elif action[0] == 'Retreat':
                                connections[self.clients[0]].selected_pokemon = action[1]

                                for c in self.clients:
                                    connections[c].message("%s retreated and switched to %s&n%s: %s I CHOOSE YOU!&n" % (connections[self.clients[0]].name, connections[self.clients[0]].selected_pokemon, connections[self.clients[0]].name, connections[self.clients[0]].selected_pokemon))

                                break

                            elif action[0] == 'Info':
                                connections[self.clients[0]].info()

                            elif action[0] != 'Back':
                                attacks = connections[self.clients[0]].pokemon_dict[connections[self.clients[0]].selected_pokemon].attacks

                                print(attacks)

                                if connections[self.clients[0]].pokemon_dict[connections[self.clients[0]].selected_pokemon].energy - attacks[int(action[0])].cost >= 0:
                                    connections[self.clients[0]].pokemon_dict[connections[self.clients[0]].selected_pokemon].energy -= attacks[int(action[0])].cost

                                    for c in self.clients:
                                        connections[c].draw(connections[self.clients[0]].selected_pokemon)
                                        connections[c].message("%s: %s, USE %s!" % (connections[self.clients[0]].name, connections[self.clients[0]].selected_pokemon, attacks[int(action[0])].name))

                                    connections[self.clients[1]].pokemon_dict[connections[self.clients[1]].selected_pokemon] = self.attack_action(connections[self.clients[1]].pokemon_dict[connections[self.clients[1]].selected_pokemon], connections[self.clients[0]].pokemon_dict[connections[self.clients[0]].selected_pokemon], attacks[int(action[0])])
                                    break
                                else:
                                    connections[self.clients[0]].message("You do not have enough energy to use this attack!")

            except:
                print(traceback.format_exc())

                self.game_running = False
                for c in self.clients:
                    connections[c].in_game = False
                    connections[c].result('Engine Error')

        return -1

        garbage_queue.put(['room', self.code])

    def set_turn(self):

        if not self.shuffled:
            self.shuffled = True
            random.shuffle(self.clients)

            connections[self.clients[0]].message('&cThe opponent has joined the match!&n&n----------&n%s&nvs&n%s&n----------&n&nStart battle!&n' % (connections[self.clients[0]].name, connections[self.clients[1]].name))
            connections[self.clients[0]].message('&cThe opponent has joined the match!&n&n----------&n%s&nvs&n%s&n----------&n&nStart battle!&n' % (connections[self.clients[1]].name, connections[self.clients[0]].name))

            for c in self.clients:
                connections[c].message('%s: %s I CHOOSE YOU!' % (connections[self.clients[0]].name, connections[self.clients[0]].selected_pokemon))
                connections[c].message('%s: %s I CHOOSE YOU!' % (connections[self.clients[1]].name, connections[self.clients[1]].selected_pokemon))

        for p in connections[self.clients[0]].pokemon_dict:
            connections[self.clients[0]].pokemon_dict[p].energy = min(50, connections[self.clients[0]].pokemon_dict[p].energy + 10)

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

    def attack_action(self, target, attacker, attack):

        base_damage = attack.damage
        message_buffer = ''

        if attacker.disabled:
            base_damage = max(0, base_damage - 10)
            message_buffer += "DAMAGE REDUCED TO %i DUE TO DISABLE!&n" % base_damage

        if base_damage > 0:
            if attacker.type == target.resistance:
                base_damage *= 0.5
                message_buffer += "IT'S NOT VERY EFFECTIVE!&n"
            elif attacker.type == target.weakness:
                base_damage *= 2
                message_buffer += "IT'S SUPER EFFECTIVE!&n"

        final_damage = base_damage

        if attack.special != 'N/A':
            if attack.special == 'stun':
                if random.randint(0, 1):
                    target.stunned = True
                    message_buffer += "%s HAS BEEN STUNNED!&n" % target.name

                else:
                    message_buffer += "%s DODGED THE STUN!&n" % target.name

            if attack.special == 'wild card':
                if random.randint(0, 1):
                    final_damage = 0
                    message_buffer = "%s MISSED! NO DAMAGE INFLICTED!&n" % attacker.name

            if attack.special == 'wild storm':
                while True:
                    if random.randint(0, 1):
                        final_damage += base_damage
                        message_buffer += "Wild Storm succeeded! Attack repeated!&n"

                    elif final_damage == base_damage:
                        final_damage = 0
                        message_buffer += 'Wild Storm missed!&n'
                        break

            if attack.special == 'disable':
                if not target.disabled:
                    message_buffer += "%s HAS BEEN DISABLED!&n" % target.name
                    target.disabled = True

                else:
                    message_buffer += "%s DODGED THE DISABLE!&n" % target.name

            if attack.special == 'recharge':
                attacker.hp = min(attacker.hptotal, attacker.hp + 20)
                message_buffer += "RECHARGE APPLIED TO %s!&n" % attacker.name

        target.hp = max(0, target.hp - final_damage)

        message_buffer += '%s INFLICTED %i DAMAGE ON %s!&n' % (attacker.name, final_damage, target.name)

        if target.hp <= 0:
            message_buffer += '%s HAS FAINTED!&n' % target.name

        if len(message_buffer) == 0:
            message_buffer = ' '

        for c in self.clients:
            connections[c].message(message_buffer)

        return target

class attack:
    def __init__(self, attack_data):
        self.name = attack_data[0]
        self.cost = int(attack_data[1])
        self.damage = int(attack_data[2])
        if len(attack_data) > 3:
            self.special = attack_data[3]
        else:
            self.special = 'N/A'

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
        attacks = []
        for num in range(0, num_attacks * 4, 4):
            attacks.append(attack(attack_data[num : num + 4]))
        return attacks

class client:
    def __init__(self, conn, addr, client_id):
        self.name = ''
        self.pokemon_dict = {}
        self.selected_pokemon = ''
        self.client_id = client_id
        self.death_time = int(time.time() + 3600)

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
        update_data = self.selected_pokemon
        for pokemon_name in self.pokemon_dict:
            update_data += ' // %s // %s // %s' % (pokemon_name, int(self.pokemon_dict[pokemon_name].hp), int(self.pokemon_dict[pokemon_name].energy))
        return update_data

    def make_action(self):
        self.out_queue.put('2 // MakeAction // %s' % self.pokemon_update())
        return self.com_get()

    def make_choose(self):
        self.out_queue.put('2 // MakeChoose // %s' % self.pokemon_update())
        return self.com_get()

    def info(self):
        self.out_queue.put('2 // Info // %s' % self.pokemon_update())

    def draw(self, m):
        self.out_queue.put('2 // Draw // %s' % m)

    def message(self, m):
        self.out_queue.put('2 // Message // %s' % m)

    def result(self, m):
        self.out_queue.put('2 // Result // %s' % m)
        
    def service(self):
        while self.alive:
            try:
                if int(time.time()) >= self.death_time:
                    self.alive = False

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
                                    if rooms[message[0]].game_running:
                                        for pokemon_name in message[1:]:
                                            self.pokemon_dict[pokemon_name] = deepcopy(pokemon_data[pokemon_name])

                                        print(self.pokemon_dict)

                                        rooms[message[0]].join(self.client_id)
                                        self.out_queue.put('1 // Success: Connected to room')
                                    else:
                                        self.out_queue.put('-1 // Error: Room Killed')
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
            garbage_queue.put(['client', self.client_id])
        except:
            pass

        return -1

    def com_read(self, conn):
        while self.alive:
            try:
                message_in = bytes.decode(conn.recv(1024), 'utf-8')

                if self.in_game and message_in == '2 // Ready':
                    print("Ready filtered")
                elif len(message_in) == 0:
                    pass
                else:
                    print('In:', message_in)
                    self.in_queue.put(message_in)
                    log_queue.put('IN: ' + message_in)

                self.death_time = int(time.time() + 3600)
            except:
                self.alive = False
                print(traceback.format_exc())

        return -1

    def com_write(self, conn):
        while self.alive:
            try:
                message_out = self.out_queue.get()
                print('Out:', message_out)
                log_queue.put('OUT: ' + message_out)
                conn.send(bytes(message_out + '\r\n', 'utf-8'))

                self.death_time = int(time.time() + 3600)
            except:
                self.alive = False
                print(traceback.format_exc())

        return -1

    def com_get(self):
        try:
            print("Read Issued")
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

            print("Read:", code, message)

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

def garbage():
    while True:
        try:
            data = garbage_queue.get()

            if data[0] == 'client':
                del connections[data[1]]
            elif data[1] == 'room':
                del rooms[data[1]]

            print('Destroyed', data[0], data[1])

        except:
            print(traceback.format_exc())

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

    PORT = random.randint(2000, 3000)

    print('STARTING RASTERA POKEMON SERVER')
    print(' | rastera.xyz')
    print(' | SERIES F2017')
    print('\nStarting server: %s:%i' % (HOST, PORT))

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Start TCP server
    server.bind((HOST, PORT))
    server.listen(1000)

    garbage_queue = Queue()
    garbage_thread = threading.Thread(target=garbage)
    garbage_thread.start()

    log_queue = Queue()
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
