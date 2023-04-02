# Echo server program
import socket
import logging

HOST = ''                 # Symbolic name meaning all available interfaces
PORT = 8888             # Arbitrary non-privileged port
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST, PORT))
    s.listen()
    conn, addr = s.accept()
    with conn:
        logging.info('Connected by %r', addr)
        print('Connected by', addr)
        while True:
            data = conn.recv(1024)
            logging.info(data)
            print(data)
            conn.sendall(data)