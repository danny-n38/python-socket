'''
client - python 3.7
'''
import sys
import pickle 
from socket import *

# server details 
serverName = 'localhost'
initServerPort = int(sys.argv[1])
serverPort = False 

## GLOBALS ## 

clientPort = int 
seq_counter = 0
logged_in = False 
currentUser = False 

## CLASSESS ## 

class command:
    def __init__(self, username, cmd, args):
        self.username = username
        self.cmd = cmd
        self.args = args

## UDP / TCP ## 

# sends message to server via UDP, returns response  
def sendUDP(data, portnum): 
    # create client socket 
    clientSocket = socket(AF_INET, SOCK_DGRAM)

    # pickle data and send over socket 
    clientSocket.sendto(pickle.dumps(data), (serverName, portnum))

    # receive reply and unpickle 
    response, serverAddress = clientSocket.recvfrom(2048)
    response = pickle.loads(response) 

    # close socket and return response object 
    clientSocket.close() 
    return response 

# sends and returns file to server via TCP 
def sendTCP(data):
    # create client socket 
    TCPclientSocket = socket(AF_INET, SOCK_STREAM)

    # connect to server via TCP 
    TCPclientSocket.connect((serverName, initServerPort))

    # send file 
    TCPclientSocket.send(data)

    # receive reply 
    reply = TCPclientSocket.recv(1024)
    
    # close particular TCP connection and return reply object 
    TCPclientSocket.close() 

    return reply 

## AUTH ## 

def reqUsername(currentUser): 
    res = sendUDP(command('auth','user',currentUser),serverPort)
    return res.args  

def reqPassword(): 
    password = input("Please enter your password: ")
    res = sendUDP(command('auth','pw',password),serverPort)
    return res.args

def reqNewPassword():
    newPw = input("Please enter a new password: ")
    res = sendUDP(command('auth','newPw',newPw),serverPort)
    return res.args

def authLogin(currentUser):
    global logged_in

    # enter username 
    user = reqUsername(currentUser) 

    # existing user
    if user == 'exist':
        pw = reqPassword()

        while pw == 'no-match':
            # incorrect password 
            pw = reqPassword()

        # logged in 
        logged_in = True
        print('Successfully logged in.') 

    # new user 
    if user == 'new':
        newPw = reqNewPassword()
        if newPw == 'done':
            logged_in = True 
            print('New account created. Logged in.')

    return 

## DISCUSSION ## 

# display available commands to user 
def selectCommand():
    print('''The following commands are available: 
    CRT: Create Thread
    LST: List Threads
    MSG: Post Message
    DLT: Delete Message,
    RDT: Read Thread
    EDT: Edit Message
    UPD: Upload File
    DWN: Download File
    RMV: Remove Thread
    XIT: Exit.'''
    )

    commands = ['CRT', 'LST', 'MSG', 'DLT', 'RDT', 'EDT', 'UPD', 'DWN', 'RMV', 'XIT']
    selection = input('Please select a command: ').split(' ', 1)

    if selection[0] in commands: 
        return commandValidation(selection)
    else:
        print('* * *')
        print('ERROR: Invalid command, please try again.')
        print('* * *')
        selectCommand()
     
def commandValidation(selection):
    if selection[0] == 'EDT': 
        args = selection[1].split(' ', 2)
    elif len(selection) > 1: 
        args = selection[1].split(' ', 1)
    else:
        args = []
    
    # create thread 
    if selection[0] == 'CRT':
        if len(args) == 1:
            data = {
                'threadtitle': args[0],
            }
            res = sendUDP(command(currentUser, 'CRT', data), serverPort)
            if res.args == 'done':
                displayPrompt('New thread created!')
            if res.args == 'error':
                displayError('Thread already exists. Please choose a different thread title')
        else:
            displayError('Use correct format - CRT threadtitle')
    
    # post message 
    if selection[0] == 'MSG':
        if len(args) == 2: 
            data = {
                'threadtitle': args[0],
                'message': args[1],
            }
            res = sendUDP(command(currentUser, 'MSG', data), serverPort)
            if res.args == 'done':
                displayPrompt('Message posted!')
            if res.args == 'no-thread':
                displayError("Thread doesn't exist. Please enter valid threadtitle")
        else: 
            displayError('Use correct format - MSG threadtitle message')
        
    # delete message 
    if selection[0] == 'DLT':
        if len(args) == 2: 
            data = {
                'threadtitle': args[0],
                'messagenumber': args[1],
            }
            res = sendUDP(command(currentUser, 'DLT', data), serverPort)
            if res.args == 'done':
                displayPrompt('Message deleted!')
            if res.args == 'no-thread':
                displayError("Thread doesn't exist. Please enter valid threadtitle")
            if res.args == 'no-msg':
                displayError("Message doesn't exist. Please enter valid messagenumber")
            if res.args == 'no-user':
                displayError("Invalid user. You can only delete your own messages")
        else: 
            displayError('Use correct format - DLT threadtitle messagenumber')
        
    # edit message 
    if selection[0] == 'EDT':
        if len(args) == 3: 
            data = {
                'threadtitle': args[0],
                'messagenumber': args[1],
                'message': args[2],
            }
            res = sendUDP(command(currentUser, 'EDT', data), serverPort)
            if res.args == 'done':
                displayPrompt('Message edited!')
            if res.args == 'no-thread':
                displayError("Thread doesn't exist. Please enter valid threadtitle")
            if res.args == 'no-msg':
                displayError("Message doesn't exist. Please enter valid messagenumber")
            if res.args == 'no-user':
                displayError("Invalid user. You can only edit your own messages")
        else: 
            displayError('Use correct format - EDT threadtitle messagenumber message')
        
    # list threads 
    if selection[0] == 'LST':
        if len(args) == 0: 
            res = sendUDP(command(currentUser, 'LST', {}), serverPort)
            threads = res.args
            print('* * *')
            if len(threads) == 0:
                print('No threads to list')
            else:
                print('Threads:')
                for thread in threads:
                    print('   - ', thread)
            print('* * *')
        else: 
            displayError('Use correct format - LST')

    # read thread
    if selection[0] == 'RDT':
        if len(args) == 1: 
            data = {
                'threadtitle': args[0],
            }
            res = sendUDP(command(currentUser, 'RDT', data), serverPort)
            if res.args == 'no-thread':
                displayError("Thread doesn't exist. Please enter valid threadtitle")
            else:
                messages = res.args
                print('* * *')
                if len(messages) == 0:
                    print('No messages in thread')
                else:
                    print('Messages in',args[0],':')
                    for message in messages:
                        print('   ', message)
                print('* * *')
            
        else: 
            displayError('Use correct format - RDT threadtitle')
    
    # upload file 
    if selection[0] == 'UPD':
        if len(args) == 2: 
            # request TCP connection 
            udp_data = {
                'threadtitle': args[0],
                'filename': args[1]
            }
            res = sendUDP(command(currentUser, 'UPD', udp_data), serverPort)
            if res.args == 'no-thread':
                displayError("Thread doesn't exist. Please enter valid threadtitle")
            if res.args == 'file-error':
                displayError('File already exists on thread')
            # TCP socket open, transfer file 
            if res.args == 'TCP-open':
                filename = args[1]
                with open(filename, 'rb') as file:
                    sendTCP(file.read(1024))
                    displayPrompt('File uploaded successfully!')
            else:
                displayError('Unable to establish TCP connection with server')
        else: 
            displayError('Use correct format - UPD threadtitle filename')
    
    # download file 
    if selection[0] == 'DWN':
        if len(args) == 2:
            # req TCP connection 
            dwn_data = {
                'threadtitle': args[0],
                'filename': args[1]
            }
            res = sendUDP(command(currentUser, 'DWN', dwn_data), serverPort)
            if res.args == 'no-thread':
                displayError("Thread doesn't exist. Please enter valid threadtitle")
            if res.args == 'file-error':
                displayError("File doesn't exist on thread. Please enter valid filename")

            # TCP socket open, transfer file 
            if res.args == 'TCP-open':
                # receive file 
                msg = 'DWN'
                file = sendTCP(msg.encode('utf-8')) 

                # download file 
                new_filename = args[1]
                with open(new_filename, 'wb') as f:
                    f.write(file)
    
                # confirmation 
                displayPrompt('File downloaded successfully!')
        else: 
            displayError('Use correct format - DWN threadtitle filename')
    
    # remove thread 
    if selection[0] == 'RMV':
        if len(args) == 1: 
            data = {
                'threadtitle': args[0],
            }
            res = sendUDP(command(currentUser, 'RMV', data), serverPort)
            if res.args == 'no-thread':
                displayError("Thread doesn't exist. Please enter valid threadtitle")
            if res.args == 'no-user':
                displayError("Invalid user. You can only remove your own threads")
            if res.args == 'done':
                displayPrompt('Thread removed!')
        else: 
            displayError('Use correct format - RMW threadtitle')

    # exit 
    if selection[0] == 'XIT':
        if len(args) == 0: 
            res = sendUDP(command(currentUser, 'XIT', {}), serverPort)
            if res.args == 'done':
                global logged_in
                logged_in = False
                displayPrompt('You have logged out!')
        else: 
            displayError('Use correct format - XIT')

# prints error message for discussion forum 
def displayError(error):
    print('* * *')
    print('ERROR: ', error)
    print('* * *')
    selectCommand()
    
# prints message 
def displayPrompt(message):
    print('* * * ')
    print(message)
    print('* * * ')

# main 
if __name__ == '__main__':

    # log in 
    while logged_in is False: 
        # contact server to receive new port number  
        while serverPort is False:
            currentUser = input("Please enter your username: ")
            res = sendUDP(command('init','newClient',currentUser), initServerPort)
            if res.args == 'newPort':
                serverPort = res.username
                # start login process 
                authLogin(currentUser)
            if res.args == 'userError':
                # username currently logged in
                print('Error: User already logged in on different client')
                break

    while logged_in:
        selectCommand()




    

 
