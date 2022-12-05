'''
server - python 3.7
'''
import sys
import pickle
import os
import _thread 
import random
from socket import * 

# server details 
serverName = 'localhost'
serverPort = int(sys.argv[1])
  
## DATA ## 

users = {}                                          # temp storage for credentials file 
clients = []                                        # list of clients 
threads = []                                        # list of threads 

UDP_on = False                                      # UDP socket open 
TCP_on = False                                      # TCP socket open  
seq_counter = 0

## CLASSES ## 

class command:
    def __init__(self, username, cmd, args):
        self.username = username
        self.cmd = cmd
        self.args = args 

## UDP/TCP ## 

# creates UDP socket and listens on port 
def UDPStart(): 
    serverSocket = socket(AF_INET, SOCK_DGRAM)
    serverSocket.bind((serverName, serverPort))

    global UDP_on
    UDP_on = True
    
    return serverSocket  

# creates TCP socket and listens on port 
def TCPStart(): 
    serverSocket = socket(AF_INET, SOCK_STREAM)
    serverSocket.bind((serverName, serverPort))

    # server in listen state 
    serverSocket.listen(1)
    
    global TCP_on
    TCP_on = True 

    return serverSocket 

## AUTH ## 
    
# reads credentials file and stores in users dict 
def loadUsers():
    global users 
    with open('credentials.txt') as file:    
        for line in file:
            (username,password) = line.split()
            users[username] = password

# check if username exists
def checkUserExists(username):
    loadUsers()                                      
    global users 
    for user in users: 
        if user == username:
            # user exists
            return True
    return False

# check if password matches 
def checkPasswordMatch(username, password):
    global users 
    if checkUserExists(username):                   # checking for user existence 
        if password == users[username]:
            return True
        else: 
            return False 
    else:
        print('user does not exist')
        return False

# create new user 
def createUser(username, password):
    if checkUserExists(username) is False:          # checking for double entries 
        entry = username + ' ' + password
        with open('credentials.txt', 'r+') as file:
            # check file for entries 
            data = file.read()
            if data:
                # credentials has entries, add new line 
                file.write('\n')
            file.write(entry)
    return True

# checks if username is currently active  
def checkClientActive(username):
    for client in clients:
        if client['username'] == username:
            if client['is_active'] is False:
                return False 
            if client['is_active'] is True:
                return True 

# login function 
def authLogin(username, serverSocket):
    while checkClientActive(username) is False:
        # receives message from client, store client's address, unpickles  
        message, clientAddress = serverSocket.recvfrom(2048)
        message = pickle.loads(message)

        # username 
        if message.cmd == 'user':
            #username = message.args

            # user exists 0
            if checkUserExists(username): 
                args = 'exist'
            # user doesn't exist
            else: 
                args = 'new'    

            # checks username and sends response 
            response = pickle.dumps(command('auth','user',args))
            serverSocket.sendto(response, clientAddress)

        # password 
        if message.cmd == 'pw':
            password = message.args
            if checkPasswordMatch(username, password) is False:
                response = pickle.dumps(command('auth','pw','no-match'))
                serverSocket.sendto(response, clientAddress)

            else: 
                response = pickle.dumps(command('auth','pw','match'))
                serverSocket.sendto(response, clientAddress)

                # logged in 
                for client in clients: 
                    if client['username'] == username:
                        client['is_active'] = True
                print(f'{username} has logged in')
                return 

        # new password 
        if message.cmd == 'newPw':
            newPassword = message.args 
            if createUser(username, newPassword): 
                response = pickle.dumps(command('auth','newPw','done'))
                serverSocket.sendto(response, clientAddress)

                # logged in 
                for client in clients: 
                    if client['username'] == username:
                        client['is_active'] = True
                print(f'{username} has registered')
                return 
    return 

## DISCUSSION FORUM ## 

# CRT: create threat 
def threadExists(threadtitle): 
    threads = os.listdir()

    if threadtitle in threads:
        return True
    else:
        return False

def crt(username, threadtitle):
    if threadExists(threadtitle):
        # thread already exists, return error msg 
        response = pickle.dumps(command(username,'CRT', 'error'))
    else:
        # create new thread 
        with open(threadtitle, 'w') as file:
            file.write(username)
        response = pickle.dumps(command(username,'CRT', 'done'))

    return response 

# MSG: post message 
def msg(username, threadtitle, message):
    if threadExists(threadtitle) is False: 
        # thread doesn't exist 
        response = pickle.dumps(command(username, 'MSG', 'no-thread'))
    elif threadExists(threadtitle): 
        # add message to thread 
        with open(threadtitle, 'r+') as file:
            lines = sum(1 for line in file)
            file.write('\n')
            content = '{} {}: {}'.format(lines,username,message)
            file.write(content)
        response = pickle.dumps(command(username, 'MSG', 'done'))

    return response 

# DLT: delete message 
def dlt(username, threadtitle, messagenumber):
    if threadExists(threadtitle) is False: 
        # thread doesn't exist 
        return (pickle.dumps(command(username, 'DLT', 'no-thread')))

    if threadExists(threadtitle):
        # find message to remove 
        msg_exists = False 
        remove = ''
        with open(threadtitle, 'r') as file:
            lines = file.readlines()
            thread_user = lines[0]
            for line in lines:
                if str(line[0]) == str(messagenumber):
                    remove = line
                    msg_exists = True 

        # invalid msg number 
        if msg_exists is False:
            return (pickle.dumps(command(username, 'DLT', 'no-msg')))

        # invalid username  
        msg_user = remove[2:].split(':')
        if username != msg_user[0]:
            return (pickle.dumps(command(username, 'DLT', 'no-user')))

        # rewrite file without message 
        with open(threadtitle, 'w') as file:
            counter = 1 
            file.write(thread_user)
            for line in lines[1:]:
                if line != remove:
                    if line[1] != ' ':
                        file.write(line[0] + line[1:])
                    else:
                        file.write(str(counter) + line[1:])
                        counter += 1
            return (pickle.dumps(command(username, 'DLT', 'done'))) 

# EDT: edit message 
def edt(username, threadtitle, messagenumber, message):
    if threadExists(threadtitle) is False: 
        # thread doesn't exist 
        return (pickle.dumps(command(username, 'EDT', 'no-thread')))

    if threadExists(threadtitle):
        # find message to edit 
        msg_exists = False 
        to_edit = ''
        with open(threadtitle, 'r') as file:
            lines = file.readlines()
            for line in lines:
                if str(line[0]) == str(messagenumber):
                    to_edit = line
                    msg_exists = True 

        # invalid msg number 
        if msg_exists is False:
            return (pickle.dumps(command(username, 'EDT', 'no-msg')))

        # invalid username  
        msg_user = to_edit[2:].split(':')
        if username != msg_user[0]:
            return (pickle.dumps(command(username, 'EDT', 'no-user')))

        # find message to edit 
        with open(threadtitle, 'w') as file:
            for line in lines:
                if str(line[0]) == str(messagenumber):
                    file.write('{} {}: {}\n'.format(messagenumber,username,message))
                else:
                    file.write(line)
            return (pickle.dumps(command(username, 'EDT', 'done'))) 

# LST: list threads
def lst():
    threads = []
    files = os.listdir()

    # files in server directory 
    for file in files: 
        temp = file.split(".")
        threads.append(temp[0])
    
    # remove credentials.py from threadlist 
    for item in threads:
        if item == 'credentials':
            threads.remove(item)

    # remove server.py from thread list 
    for item in threads:      
        if item == 'server':
            threads.remove(item)

    # remove files from threadlist 
    for thread in threads:
        if '-' in thread:
            threads.remove(thread)

    return pickle.dumps(command('','LST', threads))

# RDT: read thread 
def rdt(threadtitle):
    if threadExists(threadtitle) is False: 
        # thread doesn't exist 
        return (pickle.dumps(command('', 'RDT', 'no-thread')))
    if threadExists(threadtitle):
        messages = []
        with open(threadtitle, 'r') as file:
            lines = file.readlines()
            for line in lines[1:]:
                messages.append(line.strip())
            return (pickle.dumps(command('', 'RDT', messages)))

# RMV: remove thread 
def rmv(username, threadtitle):
    correctUser = False
    if threadExists(threadtitle) is False: 
        # thread doesn't exist 
        response = pickle.dumps(command(username, 'RDT', 'no-thread'))
    elif threadExists(threadtitle): 
        # thread exists 
        with open(threadtitle, 'r') as file:
            user = file.readline().rstrip()
            if user == username:
                correctUser = True 
            else:
                # incorrect user 
                response = pickle.dumps(command(username, 'RMV', 'no-user'))
        if correctUser:
            # remove thread
            os.remove(threadtitle)
            response = pickle.dumps(command(username, 'RMV', 'done'))
    return response

# XIT: exit 
def xit(username): 
    for client in clients:
        if client['username'] == username:
            client['is_active'] = False
            print(f'{username} has logged out')
            return pickle.dumps(command(username, 'XIT', 'done'))

# UPD: upload file 
def upd_init(username, threadtitle, filename, serverSocket, clientAddress):
    # check thread title 
    if threadExists(threadtitle) is False: 
        return serverSocket.sendto(pickle.dumps(command(username, 'UPD', 'no-thread')), clientAddress)
    
    # check files in thread 
    files = os.listdir()
    new_filename = threadtitle + '-' + filename
    for file in files: 
        if file == new_filename:
            return serverSocket.sendto(pickle.dumps(command(username, 'UPD', 'file-error')), clientAddress)

    # open TCP socket, send response to client 
    serverSocket.sendto(pickle.dumps(command(username, 'UPD', 'TCP-open')), clientAddress)
    TCPsocket = TCPStart()
    return TCPsocket  

def upd(username, threadtitle, filename, file):
    # upload file 
    new_filename = threadtitle + '-' + filename

    with open(new_filename, 'wb') as f:
        f.write(file)

    with open(threadtitle, 'a') as t:
        t.write('\n')
        t.write(username + ' uploaded ' + filename)
    
    # return confirmation 
    return True 

# DWN: download file 
def dwn_init(username, threadtitle, filename, serverSocket, clientAddress): 
    # check thread title 
    if threadExists(threadtitle) is False: 
        return serverSocket.sendto(pickle.dumps(command(username, 'DWN', 'no-thread')), clientAddress)

    # check file exists on server 
    files = os.listdir()
    new_filename = threadtitle + '-' + filename
    exists = False 
    for file in files: 
        if file == new_filename:
            exists = True 
    if exists is False: 
        return serverSocket.sendto(pickle.dumps(command(username, 'DWN', 'file-error')), clientAddress)

    # open TCP socket, send response to client 
    serverSocket.sendto(pickle.dumps(command(username, 'DWN', 'TCP-open')), clientAddress)
    TCPsocket = TCPStart()
    return TCPsocket 

def dwn(username, threadtitle, filename, connectionSocket):
    new_filename = threadtitle + '-' + filename
    
    # send file to client 
    with open(new_filename, 'rb') as file:
        connectionSocket.send(file.read(1024))

    return True 

## MULTIPLE CLIENTS ## 

# handles interaction between server and client 
def clientListenLoop(clientAddress, data, port): 
    username = data.args

    # open new udp socket for communicating with client 
    currentSocket = socket(AF_INET, SOCK_DGRAM)
    currentSocket.bind((serverName, port))
    currentSocket.settimeout(600)

    # check whether user exists and if currently active 
    exists = False 
    for client in clients: 
        if client['username'] == username:
            exists = True
            if client['is_active'] is True:
                currentSocket.sendto(pickle.dumps(command(port,'port','userError')), clientAddress)
                print('Active user attempted login on different client')
                return _thread.exit() 

    # sends temp port number to client 
    currentSocket.sendto(pickle.dumps(command(port,'port','newPort')), clientAddress)

    if exists is False:
        clients.append({
            'username': username,
            'is_active': False
        })

    while True:
        if checkClientActive(username) is False: 
            # client not active, start auth process 
            authLogin(username, currentSocket)

        if checkClientActive(username) is True: 
            # client active, start responding to commands
            message, clientAddress = currentSocket.recvfrom(2048)
            message = pickle.loads(message)

            if message.cmd == 'CRT':
                response = crt(message.username, message.args['threadtitle'])
                serverSocket.sendto(response, clientAddress)
                print(f'{username} issued {message.cmd} command')

            if message.cmd == 'MSG':
                response = msg(message.username, message.args['threadtitle'], message.args['message'])
                serverSocket.sendto(response, clientAddress)
                print(f'{username} issued {message.cmd} command')
    
            if message.cmd == 'DLT':
                response = dlt(message.username, message.args['threadtitle'], message.args['messagenumber'])
                serverSocket.sendto(response, clientAddress)
                print(f'{username} issued {message.cmd} command')

            if message.cmd == 'EDT':
                response = edt(message.username, message.args['threadtitle'], message.args['messagenumber'], message.args['message'])
                serverSocket.sendto(response, clientAddress)
                print(f'{username} issued {message.cmd} command')

            if message.cmd == 'LST':
                response = lst()
                serverSocket.sendto(response, clientAddress)
                print(f'{username} issued {message.cmd} command')

            if message.cmd == 'RDT':
                response = rdt(message.args['threadtitle'])
                serverSocket.sendto(response, clientAddress)
                print(f'{username} issued {message.cmd} command')

            if message.cmd == 'RMV':
                response = rmv(message.username, message.args['threadtitle'])
                serverSocket.sendto(response, clientAddress)
                print(f'{username} issued {message.cmd} command')

            if message.cmd == 'XIT':
                print(f'{username} issued {message.cmd} command')
                response = xit(message.username)
                serverSocket.sendto(response, clientAddress)
                return _thread.exit()  

            global TCP_on

            if message.cmd == 'UPD':
                # initiate file transfer
                username = message.username
                threadtitle = message.args['threadtitle']
                filename = message.args['filename']
                TCPserverSocket = upd_init(username, threadtitle, filename, serverSocket, clientAddress)

                while TCP_on:
                    print(f'TCP connection for {username} ready')

                    # create new socket in server for communication with client 
                    connectionSocket, address = TCPserverSocket.accept()

                    # receive file from client 
                    file = connectionSocket.recv(1024)
                    
                    # upload file to server 
                    uploaded = upd(username, threadtitle, filename, file)

                    # close TCP connection once file uploaded 
                    if uploaded:
                        connectionSocket.close()
                        TCP_on = False  
                        print(f'TCP connection for {username} closed')
                
                print(f'{username} uploaded a file')

            if message.cmd == 'DWN':
                # initiate file transfer 
                username = message.username
                threadtitle = message.args['threadtitle']
                filename = message.args['filename']
                TCPserverSocket = dwn_init(username, threadtitle, filename, serverSocket, clientAddress)

                while TCP_on: 
                    print(f'TCP connection for {username} ready')

                    # create new socket in server for communication with client 
                    connectionSocket, address = TCPserverSocket.accept()

                    # receive request from client 
                    req = connectionSocket.recv(1024)

                    # send file to client 
                    sent = dwn(username, threadtitle, filename, connectionSocket)
                    
                    # close TCP connection once file uploaded
                    if sent:
                        connectionSocket.close()
                        TCP_on = False
                        print(f'TCP connection for {username} closed')

                print(f'{username} downloaded a file')

# generates port number for new socket between server and client thread 
def portGenerator():
    used_ports = [serverPort]

    if threads != []:
        for thread in threads:
            used_ports.append(thread['port'])
    
    port = random.randint(1025,65500)

    if port not in used_ports:
        return port 
    else:
        return random.randint(min(1025,port-1),max(65500,port+1))

# main 
if __name__ == '__main__':
    # start udp 
    serverSocket = UDPStart() 
    print('Server started.')
    
    while UDP_on: 
        # receive msg from a client 
        message, clientAddress = serverSocket.recvfrom(2048)
        data = pickle.loads(message)

        if data.username == 'init' and data.cmd == 'newClient':
            # check currently used ports 
            if threads != []: 
                for thread in threads:
                    print('')

            # create new thread for client 
            port = portGenerator()
            threadId = _thread.start_new_thread(clientListenLoop, (clientAddress, data, port))

            # map username to threadid 
            threads.append({
                'threadId': threadId,
                'port': port,
            })


