import socket
import json
import threading
import time
import pickle
import rsa
import dijkstra_bellman
from controllerserver import network

CHUNK = 1024

# Load private key from file
file_pri = open('C:\Trabajo_Final_2corte_Info\pri_key.txt', 'rb')
private_key = pickle.load(file_pri)
file_pri.close()

# Load public key from file
file_pub = open('C:\Trabajo_Final_2corte_Info\pub_key.txt', 'rb')
public_key = pickle.load(file_pub)
file_pub.close()


def encrypt_message(message, public_key):
    """
    Encrypts a message using a public key.

    Parameters:
    - message (str): The message to encrypt.
    - public_key (rsa.PublicKey): The public key for encryption.

    Returns:
    - bytes: The encrypted message.
    """
    return rsa.encrypt(message, public_key)


def decrypt_message(encrypted_message, private_key):
    """
    Decrypts a message using a private key.

    Parameters:
    - encrypted_message (bytes): The encrypted message.
    - private_key (rsa.PrivateKey): The private key for decryption.

    Returns:
    - str: The decrypted message.
    """
    return rsa.decrypt(encrypted_message, private_key)


def send_message(origin_node, destination_node, message, public_key, message_type="text_message"):
    """
    Sends an encrypted message to a destination node.

    Parameters:
    - origin_node (str): The origin node.
    - destination_node (str): The destination node.
    - message (str): The message to send.
    - public_key (rsa.PublicKey): The public key for encryption.
    - message_type (str): The type of message ("text_message" or "audio_message").

    Exceptions:
    - Prints an error message if an exception occurs.
    """
    try:
        # Establish connection with the destination node
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect(("192.168.1.6", 1001))
        with open("routing_tables.json", "r") as file:
            routing_tables = json.load(file)
            if origin_node in routing_tables:
                routing_table_json = routing_tables[origin_node]
                path = routing_table_json[destination_node]

        # If it is an audio message, attach the file to the message
        if message_type == "audio_message":
            # Read the audio file and send it in parts
            with open(message, 'rb') as f:
                while True:
                    chunk = f.read(CHUNK)
                    if not chunk:
                        break
                    encrypted_chunk = encrypt_message(chunk, public_key)
                    data = {
                        "tipo": "audio_message",
                        "origen": origin_node,
                        "destino": destination_node,
                        "mensaje": encrypted_chunk
                    }
                    # Establish a new connection to send the current chunk
                    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    client_socket.connect(("192.168.1.6", 1001))
                    client_socket.sendall(pickle.dumps(data))
                    client_socket.close()

        if message_type == "text_message":
            # Encrypt only the message
            encrypted_message = encrypt_message(message.encode(), public_key)

            # Build the data information frame
            data = {
                "tipo": message_type,
                "origen": origin_node,
                "destino": destination_node,
                "mensaje": encrypted_message
            }

            # Send the frame to the destination node
            client_socket.sendall(pickle.dumps(data))

        # Close the connection
        dijkstra_bellman.visualize_path(path, network)
        client_socket.close()
    except Exception as e:
        print(f"Error sending message: {e}")


def handle_client(client_socket, private_key):
    """
    Handles incoming messages from clients.

    Parameters:
    - client_socket (socket.socket): The client socket.
    - private_key (rsa.PrivateKey): The private key for decryption.

    Exceptions:
    - Prints an error message if an exception occurs.
    """
    try:
        # Receive the message from the node
        audio_chunks = b''
        data = pickle.loads(client_socket.recv(1024))
        message_type = data.get("tipo")
        message = data.get("mensaje")

        # Decrypt the message
        decrypted_message = decrypt_message(message, private_key)

        # Process the message according to its type
        if message_type == "text_message":
            print(f"Message received from Office {data['origen']}: {decrypted_message}")

        elif message_type == "audio_message":
            print(f"Audio message received from Office {data['origen']}")
            audio_chunks += decrypted_message
            print("Audio chunk ready....")

        else:
            print("Unknown message type")

    except Exception as e:
        print(f"Error handling client: {e}")
    finally:
        # Close the connection
        client_socket.close()


def listen_messages(private_key):
    """
    Listens for incoming messages and starts a new thread for each client.

    Parameters:
    - private_key (rsa.PrivateKey): The private key for decryption.

    Exceptions:
    - Prints an error message if an exception occurs.
    """
    try:
        # Set the socket to listen to incoming messages
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind(("192.168.1.6", 1111))
        server_socket.listen(5)

        while True:
            # Accept incoming connections
            client_socket, client_address = server_socket.accept()
            print(f"Client accepted connection from {client_address}")

            # Process the message according to its type
            threading.Thread(target=handle_client, args=(client_socket, private_key)).start()

    except Exception as e:
        print(f"Error listening for messages: {e}")


if __name__ == "__main__":
    threading.Thread(target=listen_messages, args=(private_key,)).start()

    origin_node = "1.1.1.1"
    destination_node = input("Enter destination office: ")
    message_type = input("Select message type  -> text_message  //  -> audio_message  : ")

    if message_type == "text_message":
        message = input("Enter message: ")
        send_message(origin_node, destination_node, message, public_key, message_type="text_message")
    elif message_type == "audio_message":
        audio_file = "C:\Trabajo_Final_2corte_Info\Audio.wav"
        send_message(origin_node, destination_node, audio_file, public_key, message_type="audio_message")
    else:
        print("Invalid message type.")

    while True:
        time.sleep(1)
