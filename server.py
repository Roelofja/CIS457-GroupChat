"""
====================================================================
File Name   : server.py
Author(s)   : Jayden Roelofs, Chris Lamus
Class       : CIS 457
Date        : 04/10/2025
Description : 
     - This is the server component of a multi-user chat application.
     - It handles network communication using TCP sockets.
     - Features include message broadcasting, and thread handling
====================================================================
"""

import socket
from threading import Thread

# Handle communication with one client
def handleClient(sock, addr, clients):
    print(f"[+] New connection from {addr}")
    try:
        while True:
            try:
                data = sock.recv(1024)
                if not data:
                    break  # clean disconnect
            except ConnectionResetError:
                print(f"[!] Client {addr} disconnected.")
                break

            # Broadcast message to all other clients
            for client in clients:
                if client != sock:
                    try:
                        client.sendall(data)
                    except:
                        pass  # ignore broken pipe or other issues
    finally:
        print(f"[-] Closing connection from {addr}")
        if sock in clients:
            clients.remove(sock)
        sock.close()

def main():
    host = '0.0.0.0'
    port = 5000  # listen on port 5000

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(5)
    server_socket.settimeout(1.0)  # 1 second
    print(f"[+] Server listening on {host}:{port}")

    clients = []  # list to keep track of connected client sockets

    try:
        while True:
            try:
                conn, addr = server_socket.accept()
                clients.append(conn)
                t = Thread(target=handleClient, args=(conn, addr, clients))
                t.daemon = True
                t.start()
            except socket.timeout:
                continue  # allows us to break the loop with Ctrl+C
    except KeyboardInterrupt:
        print("[!] Server shutting down...")
    finally:
        for client in clients:
            client.close()
        server_socket.close()

if __name__ == "__main__":
    main()
