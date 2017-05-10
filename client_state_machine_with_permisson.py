# -*- coding: utf-8 -*-
"""
Created on Sun Apr  5 00:00:32 2015

@author: zhengzhang
"""
from chat_utils import *
import encryption as enc
import decryption as dec
import random
import pickle
#import Simon_5
#import enc_num
#import dec_num


class ClientSM:
    def __init__(self, s):
        self.state = S_OFFLINE
        self.peer = ''
        self.me = ''
        self.out_msg = ''
        self.s = s
        self.keys = self.produce_key()

    def produce_key(self):
        per_private = random.randint(1,1000)
        per_public = (base ** per_private) % p
        return (per_private, per_public)
    
    def save_public_key(self):
        try:
            public_f = open('public.dat','rb')
            public = pickle.load(public_f)
            public_f.close()
        except:
            public = {}
        public[self.get_myname()] = self.keys[1]
        public_f = open('public.dat','wb')
        pickle.dump(public,public_f)
        public_f.close()
        

    def set_state(self, state):
        self.state = state
        
    def get_state(self):
        return self.state
    
    def set_myname(self, name):
        self.me = name

    def get_myname(self):
        return self.me
        
    def connect_to(self, peer):
        msg = M_CONNECT + peer
        mysend(self.s, msg)
        response = myrecv(self.s)
        if response == (M_CONNECT+'ok'):
            self.peer = peer
            self.out_msg += 'You are connected with '+ self.peer + '\n'
            return (True)
        elif response == (M_CONNECT + 'busy'):
            self.out_msg += 'User is busy. Please try again later\n'
        elif response == (M_CONNECT + 'hey you'):
            self.out_msg += 'Cannot talk to yourself (sick)\n'
        else:
            self.out_msg += 'User is not online, try again later\n'
        return(False)

    def disconnect(self):
        msg = M_DISCONNECT
        mysend(self.s, msg)
        self.out_msg += 'You are disconnected from ' + self.peer + '\n'
        self.peer = ''

    def proc(self, my_msg, peer_code, peer_msg):
        self.out_msg = ''
#==============================================================================
# Once logged in, do a few things: get peer listing, connect, search
# And, of course, if you are so bored, just go
# This is event handling instate "S_LOGGEDIN"
#==============================================================================
        if self.state == S_LOGGEDIN:
            # todo: can't deal with multiple lines yet
            if len(my_msg) > 0:
                
                if my_msg == 'q':
                    self.out_msg += 'See you next time!\n'
                    self.state = S_OFFLINE
                    
                elif my_msg == 'time':
                    mysend(self.s, M_TIME)
                    time_in = myrecv(self.s)
                    self.out_msg += "Time is: " + time_in
                            
                elif my_msg == 'who':
                    mysend(self.s, M_LIST)
                    logged_in = myrecv(self.s)
                    self.out_msg += 'Here are all the users in the system:\n'
                    self.out_msg += logged_in
                            
                elif my_msg[0] == 'c':
                    peer = my_msg[1:]
                    peer = peer.strip()
                    mysend(self.s, M_CONNECT + peer)

                elif my_msg[0] == '?':
                    term = my_msg[1:].strip()
                    mysend(self.s, M_SEARCH + term)
                    search_rslt = myrecv(self.s)[1:].strip()
                    if (len(search_rslt)) > 0:
                        self.out_msg += search_rslt + '\n\n'
                    else:
                        self.out_msg += '\'' + term + '\'' + ' not found\n\n'
                        
                elif my_msg[0] == 'p':
                    poem_idx = my_msg[1:].strip()
                    mysend(self.s, M_POEM + poem_idx)
                    poem = myrecv(self.s)[1:].strip()
                    if (len(poem) > 0):
                        self.out_msg += poem + '\n\n'
                    else:
                        self.out_msg += 'Sonnet ' + poem_idx + ' not found\n\n'

                else:
                    self.out_msg += menu
                    
            if len(peer_msg) > 0:
                if peer_code == M_CONNSUCCESS:
                    self.peer = peer_msg
                    self.out_msg += 'You are connected with ' + self.peer 
                    self.out_msg += '. Chat away!\n\n'
                    self.out_msg += '------------------------------------\n'
                    self.state = S_CHATTING
                elif peer_code == M_CONNECT:
                    self.out_msg += peer_msg
                    to_name = peer_msg[peer_msg.index("[")+1:peer_msg.index("]")]
                    commands = ''
                    for i in range(5):
                        for j in range(4):
                            commands += random.choice(['0','1','2','3'])
                    #enc_commands = enc_num(commands)
                    mysend(self.s,M_SIMON + "(" + self.me + ") [" + to_name + "] " + commands)
                elif peer_code == M_SIMON:
                    com_str = peer_msg[peer_msg.index(")")+2:].strip()
                    from_name = peer_msg[peer_msg.index("(")+1:peer_msg.index(")")]
                    commands = []
                    for i in range(5):
                        temp = []
                        for j in range(4):
                            temp.append(int(com_str[4*i+j]))
                        commands.append(temp)
                    #dec_commands = dec_num(commands)
                    #score = Simon_5.simon(commands)
                    score = 5
                    if score == 5:
                        mysend(self.s,M_CONNSUCCESS + from_name)
                        self.out_msg += 'Yeah successfully connected to '+from_name+' !'
                    else:
                        self.out_msg += "Sorry... you didn't pass the game. Try another person!"
#==============================================================================
# Start chatting, 'bye' for quit
# This is event handling instate "S_CHATTING"
#==============================================================================
        elif self.state == S_CHATTING:
            if len(my_msg) > 0: # my stuff going out
                if my_msg[0] == '*':
                    public_f = open('public.dat','rb')
                    public_keys = pickle.load(public_f)
                    public_f.close()
                    to_name = my_msg[my_msg.index("{")+1:my_msg.index("}")]
                    my_msg = '*'+enc.encryption(my_msg[1:],self.keys[0],public_keys[to_name],p)
                mysend(self.s, M_EXCHANGE + "[" + self.me + "] " + my_msg)
                if my_msg == 'bye':
                    self.disconnect()
                    self.state = S_LOGGEDIN
                    self.peer = ''
            if len(peer_msg) > 0:    # peer's stuff, coming in
                if peer_code == M_CONNECT:
                    self.out_msg += peer_msg
                    to_name = peer_msg[peer_msg.index("[")+1:peer_msg.index("]")]
                    commands = ''
                    for i in range(5):
                        for j in range(4):
                            commands += random.choice(['0','1','2','3'])
                    #enc_commands = enc_num(commands)
                    mysend(self.s,M_SIMON + "(" + self.me + ") [" + to_name + "] " + commands)
                elif peer_code == M_SIMON:
                    com_str = peer_msg[peer_msg.index(")")+2:]
                    from_name = peer_msg[peer_msg.index("(")+1:peer_msg.index(")")]
                    commands = []
                    for i in range(5):
                        temp = []
                        for j in range(4):
                            temp.append(int(com_str[4*i+j]))
                        commands.append(temp)
                    #dec_commands = dec_num(commands)
                    #score = Simon_5.simon(commands)
                    score = 5
                    if score == 5:
                        mysend(self.s,M_CONNSUCCESS + from_name)
                        self.out_msg += 'Yeah successfully connected to '+from_name+' !'
                    else:
                        self.out_msg += "Sorry... you didn't pass the game. Try another person!"
                elif peer_code == M_CONNSUCCESS:
                    self.out_msg += "(" + peer_msg + " joined)\n"
                else:
                    if peer_msg[peer_msg.index(']')+2] == '*':
                        public_f = open('public.dat','rb')
                        public_keys = pickle.load(public_f)
                        public_f.close()
                        from_name = peer_msg[peer_msg.index('[')+1:peer_msg.index(']')]
                        temp = peer_msg[:peer_msg.index(']')+2]+dec.decryption(peer_msg[peer_msg.index(']')+3:],self.keys[0],public_keys[from_name],p)
                        peer_msg = temp
                    self.out_msg += peer_msg
            # I got bumped out
            if peer_code == M_DISCONNECT:
                self.state = S_LOGGEDIN

            # Display the menu again
            if self.state == S_LOGGEDIN:
                self.out_msg += menu
#==============================================================================
# invalid state                       
#==============================================================================
        else:
            self.out_msg += 'How did you wind up here??\n'
            print_state(self.state)
            
        return self.out_msg
