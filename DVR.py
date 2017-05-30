"""this is the main module for the routing algorithm project"""
from argparse import ArgumentParser
import socket
from threading import Thread, Lock
import time
import pickle
import math
from queue import Queue, Empty

# we don't send distance vectors every 10
# seconds rather send is_alive messagse
# cater for changed distance vectors

# global objects
SOCKET1 = socket.socket(type=socket.SOCK_DGRAM)
PRINT_LOCK = Lock()
ALIVE_MSG_QUEUE = Queue(10)
# DIS_VEC_QUEUE = Queue(10)
# each neighbor is stored as a list with router_id,cost and port
INITIAL_CONFIG_FILE = str("")
READ_CONFIG_COMP = False


#       structure of distance vector
#           destination : cost      :dictionary
#       structure of forwarding table
#           {destination : [cost , parent], }
#       structure of neighbor
#           {router_id : [cost , port], }
# #       structure of n_d_vec
#           router_id : [[dest , cost], ] 2d array

#       direct neighbors are added
#       to destinations array during
#       the initial file reading

DATA = {
    "router_id": "None",
    "port_no": "None",
    "destinations": [],
    "neighbor": {},
    "distance_vec": {},
    "n_d_vec": {},
    "forw_table": {}
}
# look for changes in forw_table after a neighbor goes down
# also the neighbor is removed from destinations

# sending is always done using pickle bytestream


def current_time():
    """helper function for returning current time"""
    return time.time()


def find_parent_close_to_source(direct_neighbors, dest, parents_array):
    """finds the parent that is the direct neighbor of source"""
    if parents_array[dest] in direct_neighbors:
        return parents_array[dest]
    else:
        find_parent_close_to_source(
            direct_neighbors, parents_array[dest], parents_array)


def identify_remote_router(remote_address):
    """
    identify the id of the remote router
    address and return it's id
    """
    port = remote_address[1]
    for key, value in DATA["neighbor"].items():
        if value[1] == port:
            return key


def prepare_for_bf(router_id, distance_vector):
    """
    this function prepares data for bellman
    ford and then calls it. it's a helper function
    """

    # debug info
    with PRINT_LOCK:
        print("inside prepare for bf on recieval from {}".format(router_id))

    # populate destination
    vertices = DATA["destinations"]
    for item in distance_vector.keys():
        if item not in vertices:
            vertices.append(item)

    # determine edges
    edges = {}
    neigh_dist_vec = DATA["n_d_vec"]
    # neigh_dist_vec is a dictionary and value below is a list
    # we have kept two copies of each edge
    for key, value in neigh_dist_vec.items():
        # value is a 2d array
        with PRINT_LOCK:
            print("prepare", key, '\n', value)
        res = {key + local_key: item[0] for local_key, item in value.items()}
        edges.update(res)
    with PRINT_LOCK:
        print("printing edges", edges)
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
    distance = dict()
    parent = dict()

    # set distance to each vertex
    # to infinity and its parent to None
    for vertex in vertices:
        distance[vertex] = math.inf
        parent[vertex] = None
    distance[source] = 0

    # now relax edges V-1 times
    for index in range(1, len(vertices) - 1):
        for edge, weight in edges.items():
            if distance[edge[0]] + weight < distance[edge[1]]:
                distance[edge[1]] = distance[edge[0]] + weight
                parent[edge[1]] = edge[0]

    # now populate forwarding table and in
    # this process we'll need to find direct neighbors
    destinations = DATA["destinations"]
    forwarding_table = DATA["forw_table"]
    direct_neighbors = [item[0] for item in DATA["neighbors"]]
    for dest in destinations:
        cost = distance[dest]
        direct_parent = find_parent_close_to_source(
            direct_neighbors, dest, parent)
        forwarding_table[dest] = [cost, direct_parent]

# reading thread for recieving incoming distance vector
# and alive messages


def recving():
    """
    this is for reading incoming data and
    alive messages and responding to them
    """
    # is alive message is responded to in place here
    global DATA, ALIVE_MSG_QUEUE

    while True:
        msg, remote = SOCKET1.recvfrom(1024)
        msg = pickle.loads(msg)

        with PRINT_LOCK:
            print("inside thread receiving")
            print(type(msg), "\n", msg)

        if msg == "is_alive":
            with PRINT_LOCK:
                print("is_alive message recieved from {}".format(
                    identify_remote_router(remote)))
            send_msg = pickle.dumps("yes" + str(DATA["port"]))
            SOCKET1.sendto(send_msg, remote)
            with PRINT_LOCK:
                print("response to is_alive send to {}".format(
                    identify_remote_router(remote)))

        elif msg.split(" ")[0] == "yes":
            ALIVE_MSG_QUEUE.put_nowait(msg)

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
            with PRINT_LOCK:
                print("distance vector recieved from {} and is : ".format(
                    remote_router_id))
                print(msg)
            prepare_for_bf(remote_router_id, msg)


def sending_distance_vectors():
    """this func runs on a separate thread\
    and is for sending distance vectors to\
    its neihbors"""
    # don't use socket.connect because it fixes a
    # remote address and causes problems when receiving
    # from other sockets and sending to them

    # we also need to cater for sending normal data

    start = current_time()
    while True:
        if(current_time() - start) < 10:
            time.sleep(2)
            continue
        else:
            data_to_send = pickle.dumps(DATA["distance_vec"])
            for value in DATA["neighbor"].values():
                send_address = ("127.0.0.1", value[1])
                SOCKET1.sendto(data_to_send, send_address)
                with PRINT_LOCK:
                    print("inside sending distance vector")
                    print("d_vec sent to {}".format(send_address))
            start = current_time()


def check_if_alive():
    """this function checks if a socket is alive or not"""
    # for identifying different alive messages responses we use port with message
    global ALIVE_MSG_QUEUE
    start = current_time()
    while True:

        if (current_time() - start) < 10:
            continue

        for key, value in DATA["neighbor"].items():
            remote = ("127.0.0.1", value[1])
            msg = pickle.dumps("is_alive" + str(value[1]))
            SOCKET1.sendto(msg, remote)
            with PRINT_LOCK:
                print("is_alive message sent to {}".format(remote))
            try:
                rcvd_msg = ALIVE_MSG_QUEUE.get(True, 2)
                if rcvd_msg.split(" ")[1] == remote[1]:
                    print("{} is alive".format(remote))
                else:
                    print("out of order msg received")
            except Empty as qu_em:
                print("no response to is_alive received from {} : {}".format(remote, qu_em))
                del DATA["neighbor"][key]
                del DATA["distance_vec"][key]
                DATA["destinations"].remove(key)
                del DATA["n_d_vec"][key]
                del DATA["forw_table"][key]
                # because our neighbor has gone down we have
                # to do something of sending new distance vec
            # except (OSError, socket.timeout) as e_ra:
            #     with PRINT_LOCK:
            #         print("{} is dead : {}".format(key, e_ra))
            #     del DATA["neighbor"][key]
            #     del DATA["distance_vec"][key]
            #     prepare_for_bf(DATA["router_id"], DATA["distance_vec"])
            #     DATA["destinations"].remove(key)
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
                    with PRINT_LOCK:
                        print("{}'s file changed".format(DATA["router_id"]))
                    list_1 = INITIAL_CONFIG_FILE.split("\n")
                    list_2 = temp.split("\n")
                    # first line that's no. of lines is never changed
                    diff = [
                        y
                        for x, y in zip(list_1, list_2)
                        if x != y
                    ]
                    for new_str in diff:
                        # we use ind - 1 because list is unordered
                        # and line no. is not included here hence
                        # index is 1 less
                        new_en = [x for x in new_str.split(" ")]
                        cost = new_en[1] = float(new_en[1])
                        port = new_en[2] = int(new_en[2])
                        router_id = new_en[0]
                        DATA["neighbor"][router_id] = [cost, port]
                    # changing n_d_vec and distance_vec
                    DATA["n_d_vec"][DATA["router_id"]] = DATA["neighbor"]
                    for key, value in DATA["neighbor"].items():
                        DATA["distance_vec"][key] = value[0]
                    INITIAL_CONFIG_FILE = temp
                    start = current_time()


def read_config_file(filename):
    """function for reading config files and storing neighbors data"""
    global INITIAL_CONFIG_FILE, DATA
    neighbors = DATA["neighbor"]
    with open(filename, "r") as file:
        # store the initial file and then go to start of file
        INITIAL_CONFIG_FILE = file.read()
        file.seek(0)
        no_of_entries = int(file.readline())
        while no_of_entries:
            temp_line = file.readline()
            arguments = temp_line.split(" ")
            neighbors[arguments[0]] = [float(arguments[1]), int(arguments[2])]
            no_of_entries -= 1
    # also adding base data to n_d_vec
    DATA["n_d_vec"][DATA["router_id"]] = DATA["neighbor"]


def initial_dvec_and_forw_insert():
    """
    function for initially filling out distance vector
    and forwarding table
    """
    global DATA
    d_vec = DATA["distance_vec"]
    for key, value in DATA["neighbor"].items():
        d_vec[key] = value[0]
        # parent to direct neighbors is always
        #  the router itself that's why DATA["router_id"]
        #  as third argument
        forw_table = DATA["forw_table"]
        forw_table[key] = [value[0], DATA["router_id"]]


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
    filename = "test\\" + args.router_config_file
    read_config_file(filename)

    # after the read_config_file func completes we set a variable
    # saying that neighbor data is ready
    global READ_CONFIG_COMP
    READ_CONFIG_COMP = True

    initial_dvec_and_forw_insert()

    SOCKET1.bind(("", DATA["port"]))  # converts the port to a listening state
    # print(DATA['neighbor'])
    # read thread is listening for incoming messages
    recv_th = Thread(target=recving, name="recv_th")
    recv_th.start()
    with PRINT_LOCK:
        print("read thread started")

    # sending thread sends its distance vector to its direct neighbors
    send_th = Thread(target=sending_distance_vectors, name="send_th")
    send_th.start()
    with PRINT_LOCK:
        print("send thread started")

    # link cost change interface thread
    intf_th = Thread(target=interface_thread, name="intf_th", args=(
        filename, ), daemon=True)
    intf_th.start()
    with PRINT_LOCK:
        print("intf thread started")

    # find thread is checking if every router is available/alive
    find_th = Thread(target=check_if_alive, name="find_th", daemon=True)
    find_th.start()
    with PRINT_LOCK:
        print("find thread started")

    # we don't need thread.join because all of our threads
    # are non daemon threads


if __name__ == "__main__":
    main()
    # SOCKET1.close()
