"""
Module to contain socket based advisor to ether work as a server or a client to load data 
"""

import socket
import logging


class SocketAdvisor:
    """SocketAdvisor utilizes sockets to run as either client or server. 
        

        The SocketAdvisor when run as a client can use sockets 
            to connect to a host server publishing data on a port.  
        The SocketAdvisor when run as a server can use sockets 
            to listen for a client sending data to the SocketAdvisor port. 
    

    Attributes:
        host: A string defining ip or host name from where the data originates.
        port: An int defining the port from which the host will be exposing data. 
    """
    def __init__(self, host="", port=8888):
        """
        Initalizes the instance based on host name and port.
           

        Parameters
        ----------
            host: string
                Ip address or host name from where the data originates. 
            port: int
             
        self.host = host
        self.port = port
        """

    def get_host(self):
        """
        Return string host value. 
        
        When SocketAdvisor is run as a client host is the ip addr/name from where data is originating. 
        
        When SocketAdvisor is run as a server host is the ip addr/name for itself (use loopback address). 
        """
        return self.host

    def set_host(self, host):
        """
        Modify the string value for host. 
        
        When SocketAdvisor is run as a client host is the ip addr/name from where data is originating. 
        
        When SocketAdvisor is run as a server host is the ip addr/name for itself (use loopback address). 
        
        Parameters
        ----------
            host: string
                Ip address or host name from where the data originates. 
        """
        self.host = host

    def get_port(self):
        """
        Return integer port value. 

        When SocketAdvisor is run as a client 
            port is refers to the port where server is publishing data. 
        
        When SocketAdvisor is run as a server 
            port refers to the port that is listening for client requests. 
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
        Open up specified port and listen until connection bonded. 
        
        Then stream all results in and yield them (return without exit)
        
        Yields
        ----------
            data: packets sent by client to SocketAdvisor
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
        Connect to specified port on server. 
        
        Then stream all results in and yield them (return without exit)
        
        Yields
        ----------
            data: packets published by server that SocketAdvisor has connected to. 
        """
        for request in requests_list:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((self.host, self.port))
                s.sendall(request.encode())
                data = s.recv(1024)
            logging.info(data)
            print("Received", repr(data))
            yield data
