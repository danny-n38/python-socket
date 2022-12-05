# Socket Programming (Python)

A basic client-server socket program that represents a messaging forum 

# Application layer message format # 

Each message between the server and client is sent as an object containing 3 values:
username, cmd, args. Depending on which stage of the interaction a client is in
(authentication/discussion), the values have different uses as shown in the markdown file. The
objects are pickled and unpickled - the values in the message specify which function to call.

Generally for each command (cmd), there are certain arguments (args) which apply. E.g. For
commands which involve a specific thread, a server will send ‘no-thread’ in args which tells the
client the thread doesn’t exist. For messages sent from client to server, args contain relevant
data such as the password, thread title, message etc.

_message protocol_ 

command {
  'username',
  'cmd',
  'args',
}

_auth_ 

username: 
  init: establish server/client connection
  auth: no active user, still authenticating 

cmd:
  user: send/receive username
  pw: send/receive password for existing user 
  newPw: send/receive password for new user 
  
 args: data
 
_forum commands_
 
 username: client's username
 cmd: 'CRT', 'MSG', 'DLT', 'EDT', 'LST', 'RDT', 'RMV', 'XIT', 'UPD', 'DWN'
 
 refer to spec for how each command is used 
 
_server response_ 
 
  done: function called successfully
  no-thread: thread doesn't exist error 
  no-msg: invalid message number error
  file-error: issue with file upload and download. file already exists, or doesn't exist (respectively) 
  TCP-open: TCP connection socket opened 
  
_client response_
  args contains data relevant for each command (refer to spec) 
  
# Program design # 
 
_Multiple concurrent clients_
 
When the server starts, a UDP socket is opened and binded to the port number specified in the
command line where it then waits for messages from clients.

When a client starts, the user enters their username and the client sends this to the server’s
socket via the specified port number. A new thread using the python_thread library is created
whenever the server receives a message from a new client address. When a new thread is
created, the server also opens a new UDP socket to communicate with this client - the port
number is randomly generated with relevant error checking, and the new port number is passed
back to the client. The client then redirects all subsequent messages to this new socket.

Inside each thread, the server first authenticates the client - client either logs in using an existing
username and password, or registers with a new username and password. Once logged in, the
server responds to all requests from each client concurrently within the respective threads. Each
thread terminates after 10 minutes without a response from the client, or when the client calls
the EXIT command.

When a user is logged into the server on one client, they won’t be able to log into the same
account on a different client - an error message will appear and the user will need to log in using
a different account.

_TCP connection_

For file upload and download, the client sends a message via UDP to the server with a request
to UPD/DWN. The server then opens a TCP socket for file transfer and informs the client. The
file is transferred via this TCP socket, which is closed as soon as transfer is complete.

_Data structures_

Information from the credentials file is read and stored in a dictionary on the server. Details of
current active clients and threads are also stored and maintained on the server as a list of
dictionaries. This includes information such as thread id, port number for thread, current active
users etc.

Data is stored as globals in server.py, and has not caused any issues when multiple clients are
interacting with the variables.

# Design reasoning and trade-offs # 

The python_thread library is used instead of the newer threading library as it’s simpler and
easier to use while still meeting all the requirements of my design. Although threading has more
functionality, this didn’t seem relevant or necessary and the use of classes would
overcomplicate the code.

A new UDP socket is created for each client thread, instead of having all communications
moving in and out of a single socket. I considered using the single socket approach as it would
use less resources and UDP is a connectionless protocol for simple transmission, however, I
had difficulty passing messages from a thread, out the single socket and to the correct client. As
such, my approach essentially mimics a TCP connection - a client connects to the server via
the main listening port. The server then passes the client’s address into a new thread where a
socket is created for communication.

Considering the design approach and trade-offs, the application meets the requirements of the
specification and can dynamically handle a varying number of concurrent clients with minimal
errors when multiple threads are interacting with the data structures.

# Issues / Possible improvements # 

I was unsuccessful in implementing reliable data transfer mechanisms to recover from loss of
UDP segments. The approaches tried:

1. ‘Checksum’: The size of each application layer message in bytes is calculated and
stored inside the message. When a message is received, the size is calculated again
and compared to the value stated. If it doesn’t match, indicate this to the sender for
retransmission

2. ‘Seq/ACK numbers and retransmission timer’: Each message contains a sequence
number. When the message is received, the receiver sends an acknowledgement to the
sender. If the sequence number is out of order, or the sender does not receive an
acknowledgement within a specified time frame, retransmit the message

Other areas for improvement:

Client timeout: each thread currently has a 10 min timeout and will close if there’s no
activity from the client. I tried to implement a ping function which periodically sends a
message to the client to check if they’re still connected. If the client acknowledges the
ping, maintain the thread and connection otherwise terminate after specified time.
Currently when a thread times out, the server continues to function as normal but the
client is not informed of the termination. Only when the client tries to send the next
command would an error message appear.
