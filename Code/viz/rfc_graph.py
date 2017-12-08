# TODO:
#      Very slow
#           - Twisted (framework)?
#           - Futures!
#           - BatchRequest
#           - Cache stuff
#      Better structure for docs, colors and labels
#           - Make interesting and useful
#      Is the graph accurate?
#      Is it a tree?
#      Multiple edges between same pair (different relationships)

import requests as rq
import networkx as nx
import matplotlib.pyplot as plt
import documents as doc
from requests_futures.sessions import FuturesSession


base = 'https://datatracker.ietf.org'
doc_cache = {}
cached_calls = 0
session = FuturesSession(max_workers=10)


def future_get_doc_url(session, resp):
    print("FUTURE: ", resp)
    body = resp.json().get('objects')[0]
    print(body.get('document'))

def get_doc_url(rfc_num):

    session.get(base + '/api/v1/doc/docalias/?name=' + rfc_num, background_callback=future_get_doc_url)

    resp = rq.get(base + '/api/v1/doc/docalias/?name=' + rfc_num)
    body = resp.json().get('objects')[0]

    return body.get('document')


def get_name(doc_url):
    resp = rq.get(base + doc_url)
    body = resp.json()

    return body.get('name')


def get_relationships(doc_name):
    resp = rq.get(base + '/api/v1/doc/relateddocument/?source=' + doc_name)
    relationships = resp.json().get('objects')

    return relationships


def get_doc(rfc_num):
    new_doc = doc.RFC(rfc_num)
    new_doc.set_draft_url(get_doc_url(new_doc.id))
    new_doc.set_draft_name(get_name(new_doc.draft_url))

    return new_doc


def find_related_docs(G, root, level):
    global cached_calls

    if level == 0:
        return

    references = []
    relationships = get_relationships(root.draft_name)
    for relationship in relationships:
        new_reference = doc.Reference()
        new_reference.set_source(root)

        target_split = relationship.get('target').split('/')
        target_doc_id = target_split[-2].upper()

        if target_doc_id in doc_cache:
            print(target_doc_id, " is cached")
            target_doc = doc_cache[target_doc_id]
            cached_calls = cached_calls + 1
        else:
            print(target_doc_id, " is not cached")
            target_doc = get_doc(target_split[-2].upper())
            doc_cache[target_doc.id] = target_doc

        new_reference.set_target(target_doc)

        type_split = relationship.get('relationship').split('/')
        new_reference.set_type(type_split[-2])

        references.append(new_reference)

    for reference in references:

        if reference.type == 'refold':
                G.add_edge(reference.source.id, reference.target.id, relType=reference.type, color='g')
        else:
            G.add_edge(reference.source.id, reference.target.id, relType=reference.type, color='b')

        find_related_docs(G, reference.target, level - 1)


def draw_graph(G):
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

    rfc_num = 'RFC' + input('Enter the requested RFC number: ')
    deg_of_separation = input('Enter the degree of separation: ')

    root_doc = get_doc(rfc_num)

    G.add_node(root_doc)
    doc_cache[root_doc.id] = root_doc

    print('\n' + ('=' * len(root_doc.draft_name)))
    print(root_doc.draft_name)
    print(('=' * len(root_doc.draft_name)) + '\n')
    print('Building graph...')

    find_related_docs(G, root_doc, int(deg_of_separation))

    print('Drawing graph...')

    draw_graph(G)

main()

total_calls = cached_calls + len(doc_cache.keys())
print("total calls: ", total_calls, " calls saved: ", cached_calls, " ", (cached_calls/total_calls)*100, "%")
