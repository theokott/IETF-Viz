import re
import networkx as nx
import matplotlib.pyplot as plt

## Returns a list of unique RFCs referenced in the document
def get_rfcs(f):
    matches = []
    for line in f:
        match = re.search("\[RFC\d*\]", line)
        if match != None:
            matches.append(match.group(0)[1:-1])
    return list(set(matches))

f = open("RFC1939.txt", "r")
rfcs = get_rfcs(f)
print(rfcs)
f.close()

g = nx.DiGraph()
g.add_node("RFC1939")
g.add_nodes_from(rfcs)

for x in rfcs:
    g.add_edge("RFC1939", x)

print(g.nodes())
print(g.edges())

labels = {"RFC1939":"RFC1939",
          "RFC1321": "RFC1321",
          "RFC1734": "RFC1734",
          "RFC821":"RFC821",
          "RFC1730":"RFC1730",
          "RFC822":"RFC822"}

pos = nx.spring_layout(g)
nx.draw_networkx_edges(g,pos,
                       g.edges(),
                       width=2,alpha=0.5,edge_color='r')
nx.draw_networkx_labels(g, pos, labels, node_size = 50)
plt.savefig("graph.png")
plt.axis("off")
plt.show()