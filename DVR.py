"""this is the main module for the routing algorithm project"""
from argparse import ArgumentParser
import socket
from threading import Thread, Lock
import time
import pickle

# global objects
SOCKET1 = socket.socket(type=socket.SOCK_DGRAM)
PRINT_LOCK = Lock()
# each neighbor is stored as a list with router_id,cost and port
INITIAL_CONFIG_FILE = str("")
READ_CONFIG_COMP = False
DATA = {"router_id": "None", "port_no": "None", "neighbor": []}

# reading thread for recieving incoming distance vector
# and alive messages
def reading():
    """this is for reading incoming data and\
    alive messages and responding to them"""
    while True:
        msg, remote = SOCKET1.recvfrom(512)
        if msg == "is_alive":
            SOCKET1.sendto("yes".encode('utf-8'), remote)
        with PRINT_LOCK:
            print(msg.decode('utf-8'))
    return

def sending():
    """this func runs on a separate thread\
    and is for sending distance vectors to\
    its neihbors"""


def interface_thread(file_name):
    """interface for changing link costs\
    the interface will be provided via looking\
    for respective file being changed and then\
    changing respective cost"""
    # this thread will first wait a few seconds
    # and then run so that the file is read is
    # for initial data by the read_config_file func
    # the initial file is stored as string by read_config_file
    global INITIAL_CONFIG_FILE
    if READ_CONFIG_COMP:
        start = time.time()
        while True:
            if (time.time() - start) < 30:
                time.sleep(5)
                continue
            else:
                file1 = open(file_name, 'r')
                temp = file1.read()
                file1.close()
                if INITIAL_CONFIG_FILE == temp:
                    time.sleep(5)
                    continue
                else:
                    list_1 = INITIAL_CONFIG_FILE.split('\n')
                    list_2 = temp.split('\n')
                    diff = [(ind, x[1]) for ind, x in enumerate(zip(list_1, list_2))
                            if x[0] != x[1]]
                    for ind, new_str in diff:
                        DATA['neighbor'].pop(ind-1)
                        new_en = [x for x in new_str.split(' ')]
                        new_en[1] = float(new_en[1])
                        new_en[2] = int(new_en[2])
                        DATA['neighbor'].insert(ind-1, new_en)
                    INITIAL_CONFIG_FILE = temp
                    start = time.time()
                # end else
            # end else
        # end while
    # end if
    return

def check_if_alive():
    """this function checks if a socket is alive or not"""
    start = time.time()
    while True:
        if (time.time() - start) < 10:
            continue
        for every_one in DATA['neighbor']:
            # every_one is a list with router_id, cost and port_no
            # .values() makes another list of the given
            remote = ('127.0.0.1', every_one[2])
            # out of the present list
            SOCKET1.sendto("is_alive".encode(), remote)
            try:
                if SOCKET1.recv(512) == "yes":
                    with PRINT_LOCK:
                        print("{} is alive".format(every_one[0]))
            except:
                with PRINT_LOCK:
                    print("{} is dead".format(every_one[0]))                                        
        start = time.time()  # ensuring the time diff is always round about 10


def read_config_file(filename):
    """function for reading config files and storing neighbors data"""
    global INITIAL_CONFIG_FILE
    with open(filename, 'r') as file:
        # store the initial file and then go to start of file
        INITIAL_CONFIG_FILE = file.read()
        file.seek(0)
        no_of_entries = int(file.readline())
        while no_of_entries:
            temp_line = file.readline()
            arguments = temp_line.split(' ')
            DATA['neighbor'].append([arguments[0], arguments[1], arguments[2]])
            no_of_entries -= 1
        # end of while
    #end of with


def main():
    """this is the main function"""
    parser = ArgumentParser()
    parser.add_argument("router_id", help="id of the router")
    parser.add_argument("port_no", help="port no. at which the\
    router is listening", type=int)
    parser.add_argument("router_config_file", help="configuration\
    file for the router")
    args = parser.parse_args()
    DATA['port'] = args.port_no
    DATA['router_id'] = args.router_id
    read_config_file(args.router_config_file)

    # after the read_config_file func completes we set a variable
    # saying that neighbor data is ready
    global READ_CONFIG_COMP
    READ_CONFIG_COMP = True

    SOCKET1.bind(('', DATA['port']))  # converts the port to a listening state
    # print(DATA['neighbor'])

    # read thread is listening for incoming messages
    read_th = Thread(target=reading)
    read_th.start()

    # sending thread sends its distance vector to its direct neighbors
    send_th = Thread(target=sending)
    send_th.start()

    # link cost change interface thread
    intf_th = Thread(target=interface_thread, args=(args.router_config_file, ), daemon=True)
    intf_th.start()

    # find thread is checking if every router is available/alive
    find_th = Thread(target=check_if_alive, daemon=True)
    find_th.start()

    # we don't need thread.join because all of our threads
    # are non daemon threads

    # SOCKET1.close()
    return


if __name__ == "__main__":
    main()
