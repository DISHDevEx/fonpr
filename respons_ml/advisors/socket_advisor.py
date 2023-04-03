"""
Module to contain socket based advisor to ether port as a server or a client to load data 
"""

import socket
import logging


class SocketAdvisor:
    def __init__(self, host="", port=8888):
        """
        Constructor to the advisor.
        Inputs: host address, port address for socket server/client desired connection
        outputs: None
        """
        self.host = host
        self.port = port

    def get_host(self):
        """
        Return host
        Input: None
        Output: host
        """
        return self.host

    def set_host(self, host):
        """
        Set host
        Input: host
        Output: none
        """
        self.host = host

    def get_port(self):
        """
        Return port
        Input: None
        Output: port
        """
        return self.port

    def set_port(self, port):
        """
        Set port
        Input: port
        Output: none
        """
        self.port = port

    def run_server(self):
        """
        Open up specified port and listen until connection bonded. Then stream all results in and yield them (return without exit)
        Input: None
        Output: List of query results
        """
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((self.host, self.port))
            s.listen()
            conn, addr = s.accept()
            with conn:
                logging.info("Connected by %r", addr)
                print("Connected by", addr)
                while True:
                    data = conn.recv(1024)
                    logging.info(data)
                    print(data)
                    yield data

    def run_client(self, requests_list):
        """
        Connect to specified server address:port, and send requests. Yield (return without exit) all results.
        Input: requests_list
        Output: List of query results
        """
        for request in requests_list:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((self.host, self.port))
                s.sendall(request.encode())
                data = s.recv(1024)
            logging.info(data)
            print("Received", repr(data))
            yield data
