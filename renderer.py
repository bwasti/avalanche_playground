import curses
import curses.textpad
import signal
import sys
from zlib import crc32
import networkx as nx


class Renderer(object):
    def __init__(self):
        pass

    def __enter__(self):

        self.stdscr = curses.initscr()
        curses.start_color()
        curses.use_default_colors()
        for i in range(0, curses.COLORS):
            curses.init_pair(i + 1, i, -1)

        self.height, self.width = self.stdscr.getmaxyx()

        self.stdscr.keypad(True)
        curses.curs_set(0)
        curses.noecho()
        curses.cbreak()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        curses.nocbreak()
        self.stdscr.keypad(False)
        curses.echo()
        curses.endwin()

    def __getattr__(self, fn):
        return getattr(curses, fn)


class NodeRenderer(object):
    def __init__(self, renderer, node):
        self.renderer = renderer
        self.node = node
        self.width = 100
        self.height = 100
        self.x = 0
        self.y = 0
        self.pad = self.renderer.newpad(self.width, self.height)

    def render(self):
        graph = nx.DiGraph()
        for t in self.node.transactions:
            graph.add_node(t)
            for parent in t.parents:
                graph.add_edge(parent, t)
        source = list(nx.topological_sort(graph))[0]
        txs = list(nx.bfs_tree(graph, source))

        seen = set()
        col = 0
        line = 0

        def get_conflict_color(tx):
            if len(self.node.conflicts[tx.utxo].transactions) > 1:
                h = crc32(str(tx.utxo).encode('utf-8'))
                return h % 50
            return 1

        def get_color(tx):
            conf = self.node.get_confidence(tx)
            return min(conf, 12) + 243

        def get_name(tx):
            name = tx.name
            return name

        for tx in txs:
            for parent in tx.parents:
                if parent in seen:
                    line += 3
                    col = 0
                    seen.clear()
            name = get_name(tx)
            self.pad.addstr(
                line + 1,
                col + 1,
                get_name(tx),
                curses.color_pair(
                    get_color(tx)))
            conflict_color = get_conflict_color(tx)
            self.pad.attron(curses.color_pair(conflict_color))
            self.renderer.textpad.rectangle(
                self.pad, line, col, line + 2, col + len(name) + 1)
            self.pad.attroff(curses.color_pair(conflict_color))
            col += len(name) + 2
            seen.add(tx)
        self.pad.refresh(
            0,
            0,
            self.y,
            self.x,
            self.renderer.height -
            1,
            self.renderer.width -
            1)


if __name__ == "__main__":
    print("try python simulator.py")
