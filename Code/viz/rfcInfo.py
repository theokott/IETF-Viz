# TODO:
#      Very slow
#      Better structure for docs, colors and labels
#      Is the graph accurate?
#      Is it a tree?

import requests as rq
import networkx as nx
import matplotlib.pyplot as plt
import Doc as doc
import Reference as ref

base = 'https://datatracker.ietf.org'

def getDocUrl(rfcNum):
    resp = rq.get(base + '/api/v1/doc/docalias/?name=' + rfcNum)
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

def generateDoc(rfcNum):
    newDoc = doc.RFC(rfcNum)
    newDoc.set_draft_url(getDocUrl(newDoc.id))
    newDoc.set_draft_name(getName(newDoc.draft_url))

    return newDoc

def generateEdges(G, root):
    return G

def find_related_docs(G, root, level):

    if level == 0:
        return

    references = []
    relationships = getRelationships(root.draft_name)
    for relationship in relationships:
        new_reference = ref.Reference()
        new_reference.set_source(root)

        target_split = relationship.get('target').split('/')
        target_doc = generateDoc(target_split[-2].upper())
        new_reference.set_target(target_doc)

        type_split = relationship.get('relationship').split('/')
        new_reference.set_type(type_split[-2])

        references.append(new_reference)

    for reference in references:

        if (reference.type == 'refold'):
                G.add_edge(reference.source.id, reference.target.id, relType=reference.type, color='g')
        else:
            G.add_edge(reference.source.id, reference.target.id, relType=reference.type, color='b')

        find_related_docs(G, reference.target, level - 1)


def drawGraph(G):
    labels = {}

    for node in G.nodes:
        labels[node] = node

    pos = nx.spring_layout(G, k=0.2, iterations=20)
    nx.draw_networkx_edges(G, pos, G.edges(), width=2, alpha=0.5, edge_color=nx.get_edge_attributes(G,'color').values())
    nx.draw_networkx_labels(G, pos, labels, node_size=50)
    plt.savefig('graph.png')
    plt.axis('off')
    plt.show()

def main():
    G = nx.Graph()

    rfcNum = 'RFC' + input('Enter the requested RFC number: ')
    rootDoc = generateDoc(rfcNum)

    G.add_node(rootDoc)

    print('\n' + ('=' * len(rootDoc.draft_name)))
    print(rootDoc.draft_name)
    print(('=' * len(rootDoc.draft_name)) + '\n')
    print('Building graph...')

    find_related_docs(G, rootDoc, 2)

    print('Drawing graph...')

    drawGraph(G)
    nx.write_dot(G, "graph.dot")

main()
