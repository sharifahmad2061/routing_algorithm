"""this is the main module for the routing algorithm project"""
from argparse import ArgumentParser
import socket
from threading import Thread, Lock
import time

SOCKET1 = socket.socket(type=socket.SOCK_DGRAM)
PRINT_LOCK = Lock()
DATA = {"router_id" : "None", "port_no" : "None", "neighbor" : []}

def reading():
    """this is for reading ind ports"""
    # global SOCKET1
    # global PRINT_LOCK
    while True:
        msg = SOCKET1.recv(100)
        with PRINT_LOCK:
            print(msg.decode('utf-8'))
    return

def read_config_file(filename):
    """function for reading config files and storing neighbors data"""
    with open(filename, 'r') as file:
        no_of_entries = file.readline()
        while no_of_entries:
            temp_line = file.readline()
            arguments = temp_line.split(' ')
            DATA['neighbor'].append({str(arguments[0]) : [arguments[1], arguments[2]]})
            no_of_entries -= 1
    return

def main():
    """this is the main function"""
    #global SOCKET1
    #global PRINT_LOCK
    parser = ArgumentParser()
    parser.add_argument("router_id", help="id of the router")
    parser.add_argument(
        "port_no", help="port no. at which the router is listening", type=int)
    parser.add_argument("router_config_file",
                        help="configuration file for the router")
    args = parser.parse_args()
    DATA['port'] = args.port_no
    DATA['router_id'] = args.router_id
    SOCKET1.bind(('', DATA['port']))

    read_th = Thread(target=reading)
    read_th.start()
    # print(args.router_id, args.port_no, args.router_config_file, sep='\n')
    DATA['neighbor'].append(int(input("sending port >>")))
    SOCKET1.connect(('127.0.0.1', DATA['neighbor'][0]))
    while True:
        PRINT_LOCK.acquire()
        ver = bool(input("do you want to continue >>"))
        PRINT_LOCK.release()
        if ver:
            SOCKET1.send("hello {} I'm {}".format(DATA['neighbor'][0], DATA['router_id'])\
            .encode('utf-8'))
            time.sleep(1)
        else:
            break
    # print(socket1.type)
    # print(socket1.getsockopt())
    SOCKET1.close()
    del globals()['SOCKET1']
    return


if __name__ == "__main__":
    main()
