# Routing_algorithm
This is a python project for implementing a routing protocol with bellman ford (distance vector) algorithm using socket and multithreaded programming.

# Project distribution
- [Asad Nawaz](github.com/asadnawaz126)

    Project research and design is part of Asad. He has to study and know about the nitty gritty of bellman ford algorithm and get an understanding of the said algorithm.
- [Sharif Ahmad](github.com/sharifahmad2061)

    Project implementation is part of Sharif where he has to implement the protocol using socket and multi threaded programming in python.

# Project specification

The file DVR.py accepts three args

    router_id           :   single capital letter                                  [string]
    port_no             :   port number on which it is listening for configuration [int]
    configuration_file  :   file containing the neighbors data                     [string]

## structure of configuration file

first line contains number of neighbors (n)

next n lines contain neighbor data

## structure of each line

space separated list of

    router_id   : id of the router                               [string]
    cost        : cost of link to this router                    [float]
    port_no     : port number that this neighbor is listening on [int]

# Project milestones

- [ ] study socket programming
- [ ] study multi threaded programming
- [ ] study bellman ford algorithm
- [ ] implement the protocol