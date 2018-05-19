import random
import copy
import time

GENESIS_NODE = None
UNIQUE_NUMBER_MAP = dict()
def get_unique_name(base):
    global UNIQUE_NUMBER_MAP
    if base in UNIQUE_NUMBER_MAP:
        UNIQUE_NUMBER_MAP[base] += 1
    else:
        UNIQUE_NUMBER_MAP[base] = 0
    return base + "_" + str(UNIQUE_NUMBER_MAP[base])

class Transaction(object):
    def __init__(self, utxo, parents, name=""):
        self.name = get_unique_name("tx") if name == "" else name
        self.utxo = utxo
        self.parents = parents
    def __repr__(self):
        return "Tx({}, {}, {})".format(
            self.utxo,
            self.parents,
            self.name)

class Node(object):
    def __init__(self, name="", alpha=0.75, k=10, beta_1=10, beta_2=10):
        self.name = get_unique_name("node") if name == "" else name

        # How many nodes to ask about each transaction
        self.k = k
        # Portion of nodes that must respond positively
        # to trust a transaction
        self.alpha = alpha
        # Confidence required for early commit
        self.beta_1 = beta_1
        # Count required for commit
        self.beta_2 = beta_2

        # Other nodes in the network
        self.nodes = set()
        # Transactions we already asked other nodes about
        self.queried = set()
        # All transactions (including ones we've never asked about)
        self.transactions = set()
        # Map of transactions to chits
        self.chits = dict()

        # Mapping of transaction UTXOs to conflict sets
        self.conflicts = dict()

    def __repr__(self):
        return "Node(" + self.name + ")"

    class ConflictSet(object):
        def __init__(self, tx):
            self.transactions = set([tx])
            self.pref = tx
            self.last = tx
            self.count = 0

        def add(self, tx):
            self.transactions.add(tx)

        def __repr__(self):
            return """ConflictSet(
  pref: {}
  last: {}
  count: {}
  txs: {}
)""".format(
                    self.pref,
                    self.last,
                    self.count,
                    self.transactions)

    def recv(self, tx):
        global GENESIS_NODE
        if not tx.parents:
            if not GENESIS_NODE:
                GENESIS_NODE = tx

        if tx not in self.transactions:
            if tx.utxo not in self.conflicts:
                self.conflicts[tx.utxo] = self.ConflictSet(tx)
            else:
                self.conflicts[tx.utxo].add(tx)
            self.transactions.add(tx)
            self.chits[tx] = 0

    def is_strongly_preferred(self, tx):
        if not tx.parents and tx is not GENESIS_NODE:
            return False

        strongly_preferred = True

        # reflexive transitive closure
        parent_set = tx.parents
        while parent_set:
            parent_set_copy = copy.copy(parent_set)
            parent_set = set()
            for parent in parent_set_copy:
                strongly_preferred &= self.conflicts[parent.utxo].pref == parent
                parent_set = parent_set.union(parent.parents)

        return strongly_preferred

    # This is inefficient
    def get_confidence(self, tx):
        confidence = self.chits[tx]
        for t in self.transactions:
            if self.chits[t] and tx in t.parents:
                confidence += self.get_confidence(t)
        return confidence

    def query(self, tx):
        self.recv(tx)
        return self.is_strongly_preferred(tx)

    def is_accepted(self, tx):
        early_commit = True
        for parent in tx.parents:
            early_commit &= self.is_accepted(parent)
        early_commit &= len(self.conflicts[tx.utxo].transactions) == 1
        early_commit &= self.get_confidence(tx) > self.beta_1
        if not early_commit:
            if self.conflicts[tx.utxo].pref == tx:
                return self.conflicts[tx.utxo].count > self.beta_2
        return early_commit

    def dump(self, tx):
        print("--- Dump of", tx, "from", self, "---")
        print("Chits", self.chits[tx])
        print("Confidence", self.get_confidence(tx))
        print(self.conflicts[tx.utxo])
        print("--- end ---")

    def run(self):
        for unqueried in self.transactions.difference(self.queried):
            # Get a random sample of the nodes in the network
            query_nodes = random.sample(self.nodes, self.k)
            positive_responses = sum([query_node.query(unqueried) for query_node in query_nodes])
            if (positive_responses >= int(self.alpha * self.k)):
                self.chits[unqueried] = 1
                for parent in unqueried.parents:
                    if self.get_confidence(parent) > self.get_confidence(self.conflicts[parent.utxo].pref):
                        self.conflicts[parent.utxo].pref = parent
                    if parent is not self.conflicts[parent.utxo].last:
                        self.conflicts[parent.utxo].last = parent
                        self.conflicts[parent.utxo].count = 0
                    else:
                        self.conflicts[parent.utxo].count += 1

            self.queried.add(unqueried)
    

class Client(object):
    def __init__(self):
        pass

# m specifies the number of times to run each node
def run_nodes(nodes, m):
    for _ in range(m):
        for node in nodes:
            node.run()

if __name__ == "__main__":

    n = Node()
    nodes = set([n])
    query = lambda tx: sum([node.query(tx2) for node in nodes])

    for _ in range(50):
        nodes.add(Node())
    for node in nodes:
        node.nodes = copy.copy(nodes)


    # As a test we are going to create a conflict
    # and make tx2 WAY more trusted than tx3
    tx0 = Transaction(0, set())
    tx1 = Transaction(1, set([tx0]))
    tx2 = Transaction(1, set([tx0]))

    # Place all the transactions in the network
    n.recv(tx0)
    run_nodes(nodes, 10)
    n.recv(tx1)
    run_nodes(nodes, 10)
    n.recv(tx2)
    run_nodes(nodes, 10)
 
    # Have everyone pile on to tx2
    for i in range(2, 24, 2):
        tx = Transaction(i, set([tx1]))
        n.recv(tx)
        run_nodes(nodes, 10)
        otx = Transaction(i+1, set([tx]))
        n.recv(otx)
        run_nodes(nodes, 10)

    n.dump(tx0)
    n.dump(tx1)
    n.dump(tx2)

    print(n.is_accepted(tx0))
    print(n.is_accepted(tx1))
    print(n.is_accepted(tx2))
