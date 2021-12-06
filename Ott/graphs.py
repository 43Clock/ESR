class Graph:
    def __init__(self, size):
        self.size = size
        self.adj = {}

    def add_edge(self, src, dest):
        if src in self.adj:
            self.adj[src].append(dest)
        else:
            self.adj[src] = [dest]

    def BFS(self, src, dest, pred):

        queue = []

        for ele in self.adj.keys():
            pred[ele] = None

        visited = {}
        visited[src] = True
        queue.append(src)

        while len(queue) != 0:
            u = queue[0]
            queue.pop(0)
            for ele in self.adj[u]:

                if ele not in visited:
                    visited[ele] = True
                    pred[ele] = u
                    queue.append(ele)

                    if ele == dest:
                        return True
        return False

    def getShortestPath(self, source, dest):
        pred = {}

        self.BFS(source, dest, pred)
        # vector path stores the shortest path
        path = []
        crawl = dest
        path.append(crawl)

        while pred[crawl] != None:
            path.append(pred[crawl])
            crawl = pred[crawl]

        return path[::-1]


# Driver program to test above functions
if __name__ == '__main__':
    # no. of vertices
    g = Graph(8)
    g.add_edge("0", "1")
    g.add_edge("0", "3")
    g.add_edge("1", "2")
    g.add_edge("3", "4")
    g.add_edge("3", "7")
    g.add_edge("4", "5")
    g.add_edge("4", "6")
    g.add_edge("4", "7")
    g.add_edge("5", "6")
    g.add_edge("6", "7")
    source = "2"
    dest = "5"
    res = g.getShortestPath(source, dest)
    print(res)
