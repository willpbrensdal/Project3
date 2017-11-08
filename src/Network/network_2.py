'''
Created on Oct 12, 2016

@author: mwitt_000
'''
import queue
import threading


## wrapper class for a queue of packets
class Interface:
    ## @param maxsize - the maximum size of the queue storing packets
    def __init__(self, maxsize=0):
        self.queue = queue.Queue(maxsize);
        self.mtu = None
    
    ##get packet from the queue interface
    def get(self):
        try:
            return self.queue.get(False)
        except queue.Empty:
            return None
        
    ##put the packet into the interface queue
    # @param pkt - Packet to be inserted into the queue
    # @param block - if True, block until room in queue, if False may throw queue.Full exception
    def put(self, pkt, block=False):
        self.queue.put(pkt, block)
        
## Implements a network layer packet (different from the RDT packet 
# from programming assignment 2).
# NOTE: This class will need to be extended to for the packet to include
# the fields necessary for the completion of this assignment.
class NetworkPacket:
    ## packet encoding lengths 
    dst_addr_S_length = 5
    flag_S_length = 1
    offset_S_length = 2
    header_length = dst_addr_S_length + flag_S_length + offset_S_length
    
    ##@param dst_addr: address of the destination host
    # @param data_S: packet payload
    def __init__(self, dst_addr, data_S):
        self.dst_addr = dst_addr
        self.data_S = data_S
        
    ## called when printing the object
    def __str__(self):
        return self.to_byte_S()
        
    ## convert packet to a byte string for transmission over links
    def to_byte_S(self):
        byte_S = str(self.dst_addr).zfill(self.dst_addr_S_length)
        byte_S += self.data_S
        return byte_S
    
    ## extract a packet object from a byte string
    # @param byte_S: byte string representation of the packet
    @classmethod
    def from_byte_S(self, byte_S):
        dst_addr = int(byte_S[0: NetworkPacket.dst_addr_S_length])
        data_S = byte_S[NetworkPacket.dst_addr_S_length:]
        return self(dst_addr, data_S)

    def to_byte_SFragment(self):
        byte_S = str(self.dst_addr).zfill(self.dst_addr_S_length)
        byte_S += str(self.flag).zfill(self.flag_S_length)
        byte_S += str(self.offset).zfill(self.offset_S_length)
        byte_S += self.data_S
        return byte_S

    @classmethod
    def is_fragment(self, byte_S):
        if byte_S[self.dst_addr_S_length] is '1':
            return True
        return False

    ## extract a packet object from a byte string
    # @param byte_S: byte string representation of the packet
    @classmethod
    def from_byte_S(self, byte_S, mtu):
        packets = []
        dst_addr = int(byte_S[0: NetworkPacket.dst_addr_S_length])
        data_S = byte_S[NetworkPacket.dst_addr_S_length:]

        # Fragment
        offset_size = 0
        while True:
            frag_flag = 1 if self.header_length + len(data_S[offset_size:]) > mtu else 0

            # self(dst_addr, data_S, 1)
            packets.append(self(dst_addr, data_S[offset_size:offset_size + mtu - self.header_length], frag_flag, offset_size))
            offset_size = offset_size + mtu - self.header_length

            if len(data_S[offset_size:]) == 0:
                break
        return packets

## Implements a network host for receiving and transmitting data
class Host:
    
    ##@param addr: address of this node represented as an integer
    def __init__(self, addr):
        self.addr = addr
        self.in_intf_L = [Interface()]
        self.out_intf_L = [Interface()]
        self.stop = False #for thread termination
    
    ## called when printing the object
    def __str__(self):
        return 'Host_%s' % (self.addr)
       
    ## create a packet and enqueue for transmission
    # @param dst_addr: destination address for the packet
    # @param data_S: data being transmitted to the network layer
    def udt_send(self, dst_addr, data_S, maxMTU):

        if len(data_S) > maxMTU:
            first_part, second_part = data_S[0:int(len(data_S) / 2)], data_S[int(len(data_S) / 2):]
            p1 = NetworkPacket(dst_addr, first_part)
            self.out_intf_L[0].put(p1.to_byte_S())  # send packets always enqueued successfully
            print('%s: sending packet "%s"' % (self, p1))
            p2 = NetworkPacket(dst_addr, second_part)
            self.out_intf_L[0].put(p2.to_byte_S())  # send packets always enqueued successfully
            print('%s: sending packet "%s"' % (self, p2))

        else:
            p = NetworkPacket(dst_addr, data_S)
            self.out_intf_L[0].put(p.to_byte_S()) # send packets always enqueued successfully
            print('%s: sending packet "%s" out interface with mtu=%d' % (self, p, self.mtu))
        
    ## receive packet from the network layer
    def udt_receive(self):
        pkt_S = self.in_intf_L[0].get()
        if pkt_S is not None:
            self.frag_buffer.append(pkt_S[NetworkPacket.header_length:])
            if not NetworkPacket.is_fragment(pkt_S):
                print('%s: received packet "%s"' % (self, ''.join(self.frag_buffer)))
                self.frag_buffer.clear()
       
    ## thread target for the host to keep receiving data
    def run(self):
        print(threading.currentThread().getName() + ': Starting')
        while True:
            # receive data arriving to the in interface
            self.udt_receive()
            # terminate
            if (self.stop):
                print(threading.currentThread().getName() + ': Ending')
                return
        


## Implements a multi-interface router described in class
class Router:
    
    ##@param name: friendly router name for debugging
    # @param intf_count: the number of input and output interfaces 
    # @param max_queue_size: max queue length (passed to Interface)
    def __init__(self, name, intf_count, max_queue_size):
        self.stop = False #for thread termination
        self.name = name
        #create a list of interfaces
        self.in_intf_L = [Interface(max_queue_size) for _ in range(intf_count)]
        self.out_intf_L = [Interface(max_queue_size) for _ in range(intf_count)]

    ## called when printing the object
    def __str__(self):
        return 'Router_%s' % (self.name)

    ## look through the content of incoming interfaces and forward to
    # appropriate outgoing interfaces
    def forward(self):
        mtu = 30
        for i in range(len(self.in_intf_L)):
            pkt_S = None
            try:
                # get packet from interface i
                pkt_S = self.in_intf_L[i].get()
                # if packet exists make a forwarding decision
                if pkt_S is not None:
                    packets = NetworkPacket.from_byte_S(pkt_S, mtu) # parse a packet out
                    for p in packets:
                        self.out_intf_L[i].put(p.to_byte_SFragment(), True)
                    print('%s: forwarding packet "%s" from interface %d to %d' % (self, p.to_byte_SFragment(), i, i))
            except queue.Full:
                print('%s: packet "%s" lost on interface %d' % (self, p, i))
                pass
                
    ## thread target for the host to keep forwarding data
    def run(self):
        print (threading.currentThread().getName() + ': Starting')
        while True:
            self.forward()
            if self.stop:
                print (threading.currentThread().getName() + ': Ending')
                return 