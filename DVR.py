from argparse import ArgumentParser
import socket
from threading import Thread, Lock
import time

def reading():
    """this is for reading ind ports"""
    global socket1
    global print_lock
    while True:
        msg = socket1.recv(100)
        with print_lock:
            print(msg.decode('utf-8'))
    return


def main():
    """this is the main function"""
    global socket1
    socket1 = socket.socket(type=socket.SOCK_DGRAM)
    port = int(input("enter port no. >>"))
    socket1.bind(('', port))
    read_th = Thread(target=reading)
    read_th.start()
    global print_lock
    print_lock = Lock()
    parser = ArgumentParser()
    parser.add_argument("router_id", help="id of the router")
    parser.add_argument(
        "port_no", help="port no. at which the router is listening", type=int)
    parser.add_argument("router_config_file",
                        help="configuration file for the router")
    args = parser.parse_args()
    print(args.router_id, args.port_no, args.router_config_file, sep='\n')
    output = int(input("sending port >>"))
    socket1.connect(('127.0.0.1', output))
    while True:
        print_lock.acquire()
        ver = bool(input("do you want to continue >>"))
        print_lock.release()
        if ver:
            socket1.send("hello {}".format(output).encode('utf-8'))
            time.sleep(1)
        else:
            break
    # print(socket1.type)
    # print(socket1.getsockopt())
    socket1.close()
    del socket1

if __name__ == "__main__":
    main()
