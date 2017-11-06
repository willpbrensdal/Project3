'''
Created on Oct 12, 2016
@author: mwitt_000
'''
from src.Network import network_3
from src.Link import link_3
import threading
from time import sleep

##configuration parameters
router_queue_size = 0 #0 means unlimited
simulation_time = 2 #give the network sufficient time to transfer all packets before quitting

# Routing tables
# List of dictionaries, where each dictionary is the table for a router, key is source, value is output interface
# 0th Index: Router A, 1st Index: Router B, 2nd Index: Router C, 3rd Index: Router D
forwarding_tables = [{1:0, 2:1},{1:0},{2:0},{1:0,2:0}]

if __name__ == '__main__':
    object_L = [] #keeps track of objects, so we can kill their threads

    #create network nodes
    client1 = network_3.Host(1)
    object_L.append(client1)
    client2 = network_3.Host(2)
    object_L.append(client2)
    client3 = network_3.Host(3)
    object_L.append(client3)
    client4 = network_3.Host(4)
    object_L.append(client4)
    router_a = network_3.Router(name='A', intf_count=2, max_queue_size=router_queue_size, forwarding_table=forwarding_tables[0])
    object_L.append(router_a)
    router_b = network_3.Router(name='B', intf_count=1, max_queue_size=router_queue_size, forwarding_table=forwarding_tables[1])
    object_L.append(router_b)
    router_c = network_3.Router(name='C', intf_count=1, max_queue_size=router_queue_size, forwarding_table=forwarding_tables[2])
    object_L.append(router_c)
    router_d = network_3.Router(name='D', intf_count=2, max_queue_size=router_queue_size, forwarding_table=forwarding_tables[3 & 4])
    object_L.append(router_d)

    #create a Link Layer to keep track of links between network nodes
    link_layer = link_3.LinkLayer()
    object_L.append(link_layer)


    #add all the links
    link_layer.add_link(link_3.Link(client1, 0, router_a, 0, 50))
    link_layer.add_link(link_3.Link(client2, 0, router_a, 1, 50))
    link_layer.add_link(link_3.Link(router_a, 0, router_b, 0, 50))
    link_layer.add_link(link_3.Link(router_a, 1, router_c, 0, 50))
    link_layer.add_link(link_3.Link(router_b, 0, router_d, 0, 50))
    link_layer.add_link(link_3.Link(router_c, 0, router_d, 1, 50))
    link_layer.add_link(link_3.Link(router_d, 0, client3, 0, 50))
    link_layer.add_link(link_3.Link(router_d, 1, client3, 0, 50))
    link_layer.add_link(link_3.Link(router_d, 0, client4, 0, 50))
    link_layer.add_link(link_3.Link(router_d, 1, client4, 0, 50))

    #start all the objects
    thread_L = []
    thread_L.append(threading.Thread(name=client1.__str__(), target=client1.run))
    thread_L.append(threading.Thread(name=client2.__str__(), target=client2.run))
    thread_L.append(threading.Thread(name=client3.__str__(), target=client3.run))
    thread_L.append(threading.Thread(name=client4.__str__(), target=client4.run))
    thread_L.append(threading.Thread(name=router_a.__str__(), target=router_a.run))
    thread_L.append(threading.Thread(name=router_b.__str__(), target=router_b.run))
    thread_L.append(threading.Thread(name=router_c.__str__(), target=router_c.run))
    thread_L.append(threading.Thread(name=router_d.__str__(), target=router_d.run))

    thread_L.append(threading.Thread(name="Network", target=link_layer.run))

    for t in thread_L:
        t.start()


    #create some send events
    for i in range(3):
        client1.udt_send(3, 'Host_1 data %d' % i)
        client2.udt_send(3, 'Host_2 data %d' % i)
    
    
    #give the network sufficient time to transfer all packets before quitting
    sleep(simulation_time)
    
    #join all threads
    for o in object_L:
        o.stop = True
    for t in thread_L:
        t.join()
        
    print("All simulation threads joined")



# writes to host periodically