"""this is the main module for the routing algorithm project"""
from argparse import ArgumentParser
import socket
from threading import Thread, Lock
import time
import pickle
import math


# global objects
SOCKET1 = socket.socket(type=socket.SOCK_DGRAM)
PRINT_LOCK = Lock()
# each neighbor is stored as a list with router_id,cost and port
INITIAL_CONFIG_FILE = str("")
READ_CONFIG_COMP = False


#       structure of distance vector
#           destination , cost
#       structure of forwarding table
#           destination , cost , parent
#       structure of neighbor
#           router_id , cost , port

#       direct neighbors are added
#       to destinations array during
#       the initial file reading

DATA = {
    "router_id": "None",
    "port_no": "None",
    "destinations": [],
    "neighbor": [],
    "distance_vec": [],
    "n_d_vec": {},
    "forw_table": []
}


# sending is always done using pickle bytestream


def current_time():
    """helper function for returning current time"""
    return time.time()


def identify_remote_router(remote_address):
    """
    identify the id of the remote router
    address and return it's id
    """
    global DATA
    port = remote_address[1]
    for every_router in DATA["neighbor"]:
        if every_router[2] is port:
            return every_router[0]


def prepare_for_bf(router_id, distance_vector):
    """
    this function prepares data for bellman
    ford and then calls it. it's a helper function
    """
    global DATA

    # populate destination
    vertices = DATA["destinations"]
    for item in distance_vector:
        if item[0] not in vertices:
            vertices.append(item[0])

    # determine edges
    edges = {}
    neigh_dist_vec = DATA["n_d_vec"]
    # neigh_dist_vec is a dictionary and value below is a list
    # we have kept two copies of each edge
    for key, value in neigh_dist_vec.items():
        res = {key+item[0]: item[1] for item in value}
        edges.update(res)

    # starting vertex
    source = DATA["router_id"]

    # call bellman ford now
    bellman_ford(vertices, edges, source)




def bellman_ford(vertices, edges, source):
    """
    bellman ford algorithm is run as soon
    as a distance vector is recieved but first
    prepare_for_bf is called and data is prepared
    for bellman ford algorithm
    """


# reading thread for recieving incoming distance vector
# and alive messages
def recving():
    """
    this is for reading incoming data and
    alive messages and responding to them
    """
    global SOCKET1
    global PRINT_LOCK
    global DATA
    while True:
        msg, remote = SOCKET1.recvfrom(1024)
        msg = pickle.loads(msg)

        if msg is "is_alive":
            send_msg = pickle.dumps("yes")
            SOCKET1.sendto(send_msg, remote)

        else:
            # find who the remote sender is and
            # pass information to the bellman ford algorithm
            remote_router_id = identify_remote_router(remote)
            # when we receive a distance vector
            # it means there is some change in
            # it therefore we don't need to check
            # if there is any change or not and
            # hence assign it directly
            DATA["n_d_vec"][remote_router_id] = msg
            prepare_for_bf(remote_router_id, msg)


def sending():
    """this func runs on a separate thread\
    and is for sending distance vectors to\
    its neihbors"""
    # don't use socket.connect because it fixes a
    # remote address and causes problems when receiving
    # from other sockets and sending to them

    # we also need to cater for sending normal data

    global DATA
    start = current_time()
    while True:
        if(current_time() - start) < 10:
            time.sleep(2)
            continue
        else:
            data_to_send = pickle.dumps(DATA["distance_vec"])
            for every_neighbor in DATA["neighbor"]:
                send_address = ("127.0.0.1", every_neighbor[2])
                SOCKET1.sendto(data_to_send, send_address)
            start = current_time()


def check_if_alive():
    """this function checks if a socket is alive or not"""
    global SOCKET1
    global PRINT_LOCK
    global DATA
    start = current_time()
    msg = pickle.dumps("is_alive")
    while True:

        if (current_time() - start) < 10:
            continue

        for every_one in DATA["neighbor"]:
            remote = ("127.0.0.1", every_one[2])
            # out of the present list
            # decrease waiting time
            SOCKET1.settimeout(2)
            SOCKET1.sendto(msg, remote)
            try:
                recv_msg = pickle.loads(SOCKET1.recvfrom(512)[0])
                if recv_msg is "yes":
                    with PRINT_LOCK:
                        print("{} is alive".format(every_one[0]))
            except (OSError, socket.timeout) as e_ra:
                # reset waiting time
                SOCKET1.settimeout(socket.getdefaulttimeout())
                with PRINT_LOCK:
                    print("{} is dead : {}".format(every_one[0], e_ra))
                index = DATA["neighbor"].index(every_one)
                DATA["neighbor"].pop(index)
                index = DATA["distance_vec"].index(
                    [every_one[0], every_one[1]])
                DATA["distance_vec"].pop(index)
                bellman_ford(DATA["router_id"], DATA["distance_vec"])
        # ensuring the time diff is always round about 10
        start = current_time()


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
    global READ_CONFIG_COMP

    if READ_CONFIG_COMP:
        start = current_time()
        while True:
            if (current_time() - start) < 30:
                time.sleep(5)
                continue
            else:
                file1 = open(file_name, "r")
                temp = file1.read()
                file1.close()
                if INITIAL_CONFIG_FILE == temp:
                    start = current_time()
                    continue
                else:
                    list_1 = INITIAL_CONFIG_FILE.split("\n")
                    list_2 = temp.split("\n")
                    # first line that's no. of lines is never changed
                    diff = [
                        (ind, x[1])
                        for ind, x in enumerate(zip(list_1, list_2))
                        if x[0] != x[1]
                    ]
                    for ind, new_str in diff:
                        # we use ind - 1 because list is unordered
                        # and line no. is not included here hence
                        # index is 1 less
                        DATA["neighbor"].pop(ind - 1)
                        new_en = [x for x in new_str.split(" ")]
                        new_en[1] = float(new_en[1])
                        new_en[2] = int(new_en[2])
                        DATA["neighbor"].insert(ind - 1, new_en)
                    # inserting new base router data to n_d_vec
                    DATA["n_d_vec"][DATA["router_id"]] = DATA["neighbor"]
                    INITIAL_CONFIG_FILE = temp
                    start = current_time()


def read_config_file(filename):
    """function for reading config files and storing neighbors data"""
    global INITIAL_CONFIG_FILE
    global DATA
    with open(filename, "r") as file:
        # store the initial file and then go to start of file
        INITIAL_CONFIG_FILE = file.read()
        file.seek(0)
        no_of_entries = int(file.readline())
        while no_of_entries:
            temp_line = file.readline()
            arguments = temp_line.split(" ")
            DATA["neighbor"].append(
                [arguments[0], float(arguments[1]), int(arguments[2])])
            no_of_entries -= 1
    # also adding base data to n_d_vec
    DATA["n_d_vec"][DATA["router_id"]] = DATA["neighbor"]


def initial_dvec_and_forw_insert():
    """
    function for initially filling out distance vector
    and forwarding table
    """
    global DATA
    for every_neighbor in DATA["neighbor"]:
        DATA["distanc_vec"].append([every_neighbor[0], every_neighbor[1]])
        # parent to direct neighbors is always
        #  the router itself that's why DATA["router_id"]
        #  as third argument
        DATA["forw_table"].append(
            [every_neighbor[0], every_neighbor[1], DATA["router_id"]])


def main():
    """this is the main function"""
    parser = ArgumentParser()
    parser.add_argument("router_id", help="id of the router")
    parser.add_argument("port_no", help="port no. at which the\
    router is listening", type=int)
    parser.add_argument("router_config_file", help="configuration\
    file for the router")
    args = parser.parse_args()
    DATA["port"] = args.port_no
    DATA["router_id"] = args.router_id
    read_config_file(args.router_config_file)

    # after the read_config_file func completes we set a variable
    # saying that neighbor data is ready
    global READ_CONFIG_COMP
    READ_CONFIG_COMP = True

    initial_dvec_and_forw_insert()

    SOCKET1.bind(("", DATA["port"]))  # converts the port to a listening state
    # print(DATA['neighbor'])

    # read thread is listening for incoming messages
    recv_th = Thread(target=recving)
    recv_th.start()

    # sending thread sends its distance vector to its direct neighbors
    send_th = Thread(target=sending)
    send_th.start()

    # link cost change interface thread
    intf_th = Thread(target=interface_thread, args=(
        args.router_config_file, ), daemon=True)
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
