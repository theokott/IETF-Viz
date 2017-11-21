## TODO:
##      Objects?
##      Recursive calls
##      Better structure for docs, colors and labels

import requests as rq
import networkx as nx
import matplotlib.pyplot as plt

base = 'https://datatracker.ietf.org'

def getDocUrl(rfcNum):
    resp = rq.get(base + '/api/v1/doc/docalias/?name=RFC' + rfcNum)
    body = resp.json().get('objects')[0]

    return body.get('document')

def getName(docUrl):
    resp = rq.get(base + docUrl)
    body = resp.json()

    return body.get('name')

def getRelationships(docName):
    resp = rq.get(base + '/api/v1/doc/relateddocument/?source=' + docName)
    relationships = resp.json().get('objects')

    return relationships

def main():
    G = nx.Graph()
    rfcNum = input("Enter the requested RFC number: ")
    docUrl = getDocUrl(rfcNum)
    docName = getName(docUrl)
    labels = {}
    colors = []

    print('\n' + ('=' * len(docName)))
    print(docName)
    print(('=' * len(docName)) + '\n')

    relationships = getRelationships(docName)

    relDocs = []

    for rel in relationships:
        ## print rel
        relType = rel.get('relationship').split('/')[-2]
        name = getName(rel.get('target')).upper()
        relDocs.append((name, relType))

    print('RELDOCS:')
    print(relDocs)


    for relDoc in relDocs:
        print(relDoc)
        print(relDoc[1] == 'refold')

        if (docName, relDoc[0]) not in G.edges:
            if (relDoc[1] == 'refold'):
                    G.add_edge(docName, relDoc[0], relType=relDoc[1], color='g')
            else:
                G.add_edge(docName, relDoc[0], relType=relDoc[1], color='b')

    print('\nNODES:\n')
    for node in G.nodes:
        labels[node] = node
        print(node)


    print('\nEDGES:\n')
    for edge in G.edges:
        print(edge)
        print(G[edge[0]][edge[1]]['relType'])
        print(G[edge[0]][edge[1]]['color'])

    pos = nx.spring_layout(G)
    nx.draw_networkx_edges(G, pos, G.edges(), width=2, alpha=0.5, edge_color=nx.get_edge_attributes(G,'color').values())
    nx.draw_networkx_labels(G, pos, labels, node_size=50)
    plt.savefig("graph.png")
    plt.axis("off")
    plt.show()

main()
