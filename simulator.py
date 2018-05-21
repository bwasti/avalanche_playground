from avalanche import Node, Transaction, run_nodes
from renderer import Renderer, NodeRenderer
import copy
import random
import time


class Client(object):
    def __init__(self, nodes):
        self.nodes = nodes
        self.history = []

    def send(self, tx):
        self.history.append(tx)
        for node in self.nodes:
            node.recv(tx)


class Simulator(object):
    def run_nodes(self, m):
        for _ in range(m):
            for node in self.nodes:
                node.run()

    def __init__(self, num_nodes=100):
        self.primary_node = Node()
        self.nodes = set([self.primary_node])
        for _ in range(num_nodes - 1):
            self.nodes.add(Node())
        for node in self.nodes:
            node.nodes = copy.copy(self.nodes)

    def spawn_client(self, num_nodes=10):
        # give the client a random set of nodes
        client_nodes = copy.copy(random.sample(self.nodes, num_nodes))
        return Client(client_nodes)


if __name__ == "__main__":
    s = Simulator()
    c = s.spawn_client()

    # As a test we are going to create a conflict
    # and make tx1 WAY more trusted than tx2
    tx0 = Transaction(0, set())
    tx1 = Transaction(1, set([tx0]))
    tx2 = Transaction(1, set([tx0]))
    c.send(Transaction(2, set([tx1])))
    c.send(Transaction(3, set([tx1])))

    # Place all the transactions in the network
    c.send(tx0)
    c.send(tx1)
    c.send(tx2)

    with Renderer() as r:
        nr = NodeRenderer(r, s.primary_node)

        # Have everyone pile on to tx1
        for i in range(2, 24, 2):
            tx = Transaction(i, set([tx1]))
            c.send(tx)
            otx = Transaction(i + 1, set([tx]))
            c.send(otx)
            s.run_nodes(10)
            nr.render()
            time.sleep(0.4)
        time.sleep(10)
