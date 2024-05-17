import socket
import json
import threading
import time
import pickle
import rsa

# Load private key from file
file_pri = open('C:\Trabajo_Final_2corte_Info\pri_key.txt', 'rb')
private_key = pickle.load(file_pri)
file_pri.close()

# Load public key from file
file_pub = open('C:\Trabajo_Final_2corte_Info\pub_key.txt', 'rb')
public_key = pickle.load(file_pub)
file_pub.close()


class TCPNode:
    """
    A class to represent a TCP Node in a network.

    Attributes:
    - node_name (str): The name of the node.
    - server_host (str): The host address of the controller server.
    - server_port (int): The port of the controller server.
    - listen_port (int): The port the node listens on for incoming connections.
    - outgoing_ports (list of int): A list of ports for outgoing connections.
    - routing_table (dict): The routing table for the node.
    - client_port (int): The port for client connections.
    - port_mapping (dict): The mapping of node names to ports.

    Methods:
    - start(): Starts the server and connects to the controller server.
    - connect_to_server(): Connects to the controller server to obtain the routing table.
    - accept_connections(): Accepts incoming connections from other nodes.
    - handle_client(client_socket): Handles incoming messages from other nodes.
    - connect_to_node(destination_node_name, position, message): Connects to another node and sends a message.
    - handle_text_message(message_type, origin_node, destination_node, text_message): Handles text messages.
    - route_message(destination_node_name, message): Routes messages to their destination based on the routing table.
    """
    def __init__(self, node_name, server_host, server_port, listen_port, outgoing_ports):
        """
        Initializes the TCPNode with node details and loads the port mapping.

        Parameters:
        - node_name (str): The name of the node.
        - server_host (str): The host address of the controller server.
        - server_port (int): The port of the controller server.
        - listen_port (int): The port the node listens on for incoming connections.
        - outgoing_ports (list of int): A list of ports for outgoing connections.
        """
        self.node_name = node_name
        self.server_host = server_host
        self.server_port = server_port
        self.listen_port = listen_port
        self.outgoing_ports = outgoing_ports
        self.routing_table = None
        self.client_port = client_port
        # Load port mapping
        with open("port_mapping.json", "r") as file:
            self.port_mapping = json.load(file)

    def start(self):
        """
        Starts the server and connects to the controller server.

        This method initializes the server socket to listen for incoming connections
        and starts a thread to handle these connections. It also connects to the
        controller server to obtain the routing table.
        """
        # Start server for incoming connections
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind(("192.168.1.6", self.listen_port))
        self.server_socket.listen(5)
        print(f"Office {self.node_name} listening on port {self.listen_port} //.....:")

        # Connect to the controller server to obtain the routing tables
        self.connect_to_server()

        # Listen for incoming connections from other nodes in separate threads
        threading.Thread(target=self.accept_connections).start()

    def connect_to_server(self):
        """
        Connects to the controller server to obtain the routing table.

        This method establishes a connection to the controller server, sends the
        node name encrypted with the public key, and receives the routing table.
        """
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect((self.server_host, self.server_port))
            encrypted_node_name = rsa.encrypt(self.node_name.encode(), public_key)
            client_socket.sendall(encrypted_node_name)
            routing_table_json = client_socket.recv(4096).decode()
            # Save the received routing table
            self.routing_table = json.loads(routing_table_json)
            client_socket.close()
            # print(f"ACK received from controller.")
            # print(f"ACK received from controller :", self.routing_table )

        except Exception as e:
                print(f"Error while connecting to server: {e}")

    def accept_connections(self):
        """
        Accepts incoming connections from other nodes.

        This method runs in a separate thread and continuously accepts incoming
        connections, creating a new thread to handle each connection.
        """
        while True:
            try:
                client_socket, client_address = self.server_socket.accept()
                print(f"Node {self.node_name} accepted connection from {client_address}")
                threading.Thread(target=self.handle_client, args=(client_socket,)).start()
            except Exception as e:
                print(f"Error accepting connection: {e}")

    def handle_client(self, client_socket):
        """
        Handles incoming messages from other nodes.

        This method receives and processes messages from connected nodes, and
        closes the connection after processing.

        Parameters:
        - client_socket (socket.socket): The socket connected to the client.
        """
        try:
            data = client_socket.recv(1024)
            message_data = pickle.loads(data)
            message_type = message_data.get("tipo")
            origin_node = message_data.get("origen")
            destination_node = message_data.get("destino")
            text_message = message_data.get("mensaje")

            # Call the method that handles the user message
            self.handle_text_message(message_type, origin_node, destination_node, text_message)

        except Exception as e:
            print(f"Error handling client: {e}")
        finally:
            client_socket.close()

    def connect_to_node(self, destination_node_name, position, message):
        """
        Connects to another node and sends a message.

        This method establishes a connection to another node based on the position
        in the outgoing ports list and sends the specified message.

        Parameters:
        - destination_node_name (str): The name of the destination node.
        - position (int): The index of the outgoing port in the list.
        - message (str): The message to be sent.
        """
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect(("192.168.1.6", self.outgoing_ports[position]))
            client_socket.sendall(destination_node_name.encode())
            print(f"{self.node_name} connected to {destination_node_name} on port {self.outgoing_ports[position]}")
            # Call the method that handles the user message
            client_socket.sendall(message.encode())
            # Send a message to the destination node
            client_socket.close()
        except Exception as e:
            print(f"Error while connecting to node {destination_node_name} on port {self.outgoing_ports[position]}: {e}")

    def handle_text_message(self, message_type, origin_node, destination_node, text_message):
        """
        Handles text messages.

        This method processes the received text message and forwards it using
        the route_message method.

        Parameters:
        - message_type (str): The type of the message.
        - origin_node (str): The name of the origin node.
        - destination_node (str): The name of the destination node.
        - text_message (str): The text message to be handled.
        """
        print(f"Received user message from {origin_node} to {destination_node}....:::: '{text_message}'")

        # Forward user message using route_message
        self.route_message(destination_node, {
            "tipo": message_type,
            "origen": origin_node,
            "destino": destination_node,
            "mensaje": text_message
        })

    def route_message(self, destination_node_name, message):
        """
        Routes messages to their destination based on the routing table.

        This method determines the next hop for the message based on the routing
        table and sends the message to the next hop.

        Parameters:
        - destination_node_name (str): The name of the destination node.
        - message (dict): The message to be routed.
        """
        # Check if the destination node is in the routing table
        if destination_node_name in self.routing_table:
            # Get the shortest path to the destination node
            path_to_destination = self.routing_table[destination_node_name]

            # Check if the path is valid
            if len(path_to_destination) > 1:
                # Get the next hop
                next_hop = path_to_destination[1]
                # Get the output port for the next hop from the port_mapping dictionary
                next_hop_port = self.port_mapping[next_hop]

                if next_hop_port is not None:
                    # Establish connection to next hop
                    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    client_socket.connect(("192.168.1.6", next_hop_port))
                    # Send the message to the next hop
                    client_socket.sendall(pickle.dumps(message))

                    print(f"Office {self.node_name} routed message to {destination_node_name} at hop {next_hop}")

                else:
                    print(f"No outgoing port found for next hop {next_hop}.")
            else:
                # If the current node is the destination node,
                # send the message back to the receiving client
                print(f"The Office {self.node_name} is the destination... the message was sent to the client.")
                client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                # Establish the connection with the client
                client_socket.connect(("192.168.1.6", client_port))
                client_socket.sendall(pickle.dumps(message))
                # Close connection
                client_socket.close()
        else:
            print(f"No route found to {destination_node_name}")


if __name__ == "__main__":
    node_name = "7.7.7.7"
    server_host = "192.168.1.6"
    client_port = 7777
    server_port = 1234
    listen_port = 1007
    outgoing_ports = [1005,1008,1010]
    node = TCPNode(node_name, server_host, server_port, listen_port, outgoing_ports)
    node.start()

    while True:
        node.connect_to_server()
        time.sleep(15)