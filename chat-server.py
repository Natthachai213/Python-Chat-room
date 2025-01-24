import threading
import socket

# Server setup parameters
host = "192.168.11.182"  # Local IP for the server (adjust if needed)
port = 8080  # Port to listen on

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Bind the server to IP address and port
server.bind((host, port))
# Start listening for incoming connections
server.listen()

# List to store connected clients and their nicknames
clients = []
nicknames = []


# 1. Broadcasting Method: Send a message to all clients
def broadcast(message):
    for client in clients:
        try:
            client.send(message)
        except socket.error:
            continue  # Skip if error occurs while sending to a client


# 2. Handle individual client connections (receiving and responding)
def handle(client):
    while True:
        try:
            msg = client.recv(1024)
            if not msg:
                break  # If no message is received, client has disconnected

            decoded_msg = msg.decode('ascii')

            if decoded_msg.startswith('KICK'):
                if nicknames[clients.index(client)] == 'admin':
                    name_to_kick = decoded_msg[5:]
                    kick_user(name_to_kick)
                else:
                    client.send('Command Refused! Only admin can use this command.'.encode('ascii'))

            elif decoded_msg.startswith('BAN'):
                if nicknames[clients.index(client)] == 'admin':
                    name_to_ban = decoded_msg[4:]
                    kick_user(name_to_ban)
                    with open('bans.txt', 'a') as f:
                        f.write(f'{name_to_ban}\n')
                    print(f'{name_to_ban} was banned by the Admin!')
                else:
                    client.send('Command Refused! Only admin can use this command.'.encode('ascii'))

            else:
                broadcast(msg)  # Broadcast received message to all clients

        except socket.error:
            break  # If socket error occurs, break the loop

    # Clean up when a client disconnects
    if client in clients:
        index = clients.index(client)
        nickname = nicknames[index]
        clients.remove(client)
        nicknames.remove(nickname)
        broadcast(f'{nickname} left the Chat!'.encode('ascii'))
        client.close()


# Main method to accept clients and handle connections
def receive():
    while True:
        try:
            client, address = server.accept()
            print(f"Connected with {str(address)}")

            # Ask the client for a nickname
            client.send('NICK'.encode('ascii'))
            nickname = client.recv(1024).decode('ascii')

            # Check if the nickname is banned
            with open('bans.txt', 'r') as f:
                bans = f.readlines()

            if nickname + '\n' in bans:
                client.send('BAN'.encode('ascii'))
                client.close()
                continue

            # Admin login (password required)
            if nickname == 'admin':
                client.send('PASS'.encode('ascii'))
                password = client.recv(1024).decode('ascii')
                if password != 'adminpass':  # Simple password check
                    client.send('REFUSE'.encode('ascii'))
                    client.close()
                    continue

            # Add client to list
            nicknames.append(nickname)
            clients.append(client)

            print(f'Nickname of the client is {nickname}')
            broadcast(f'{nickname} joined the Chat'.encode('ascii'))
            client.send('Connected to the Server!'.encode('ascii'))

            # Handle the client in a separate thread to allow multiple clients
            thread = threading.Thread(target=handle, args=(client,))
            thread.start()

        except socket.error as e:
            print(f"Error accepting new client: {e}")
            continue


# Method to kick a user by their nickname
def kick_user(name):
    if name in nicknames:
        name_index = nicknames.index(name)
        client_to_kick = clients[name_index]
        clients.remove(client_to_kick)
        nicknames.remove(name)
        client_to_kick.send('You were kicked from the Chat!'.encode('ascii'))
        client_to_kick.close()
        broadcast(f'{name} was kicked from the server!'.encode('ascii'))


# Start the server
print('Server is Listening ...')
receive()
