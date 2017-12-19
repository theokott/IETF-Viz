# TODO:
#      Very slow
#           - Cache stuff in memory/disk
#           - Calls still used to get the relationships between docs. Need to cache these.
#      Better structure for docs, colors and labels
#           - Make interesting and useful
#           - Multiple references between same pair of docs overlap
#           - Still need to add that info to the actual classes...
#      Is the graph accurate?
#      Is it a tree?
#      Smarten up code
#           - references used too much in future_get_related_docs()
#           - is there a way to recursively call asynchronously?
#           - Lambda func for passing args to callback?
import requests as rq
import networkx as nx
import matplotlib.pyplot as plt
import documents as doc
from requests_futures.sessions import FuturesSession
import _pickle as pickle

base = 'https://datatracker.ietf.org'

# A dictionary of RFCs indexed on the id of the RFC (such as doc_cache['RFC1939'])
doc_cache = {}
# A dictionary of References indexed on the id of the source RFC
# (such as reference_cache[ref.source.id] or reference_cache['RFC1939'])
reference_cache = {}
cached_calls = 0
uncached_calls = 0
session = FuturesSession(max_workers=50)


def get_target_doc(sess, resp):

    # N.B. the data stored in the field 'name' in the JSON is actually the RFC Number and thus a unique ID.
    # The name of the draft that became the RFC is contained within the URL. This can be identical to the RFC Number

    body = resp.json().get('objects')[0]
    doc_id = body.get('name').upper()
    doc_url = body.get('document')
    split_url = doc_url.split('/')
    doc_name = split_url[-2]

    new_doc = doc.RFC(doc_id)
    new_doc.set_draft_url(doc_url)
    new_doc.set_draft_name(doc_name)

    doc_cache[new_doc.id] = new_doc


def get_doc_url(rfc_num):
    session.get(base + '/api/v1/doc/docalias/?name=' + rfc_num, background_callback=get_target_doc)

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

    if rfc_num in doc_cache.keys():
        return doc_cache[rfc_num]

    else:
        new_doc = doc.RFC(rfc_num)
        new_doc.set_draft_url(get_doc_url(new_doc.id))
        new_doc.set_draft_name(get_name(new_doc.draft_url))

        return new_doc


def add_reference_to_graph(G, reference):
    if reference.type == 'refold':
        G.add_edge(reference.source.id, reference.target.id, relType=reference.type, color='g', style='dashdot')
    else:
        G.add_edge(reference.source.id, reference.target.id, relType=reference.type, color='b', style='dashdot')


def get_related_docs(root):
    global cached_calls
    global uncached_calls
    futures = []
    incomplete_references = []
    references = []

    relationships = get_relationships(root.draft_name)

    for relationship in relationships:
        new_reference = doc.Reference()
        new_reference.set_source(root)

        type_split = relationship.get('relationship').split('/')
        new_reference.set_type(type_split[-2])

        target_split = relationship.get('target').split('/')
        target_doc_id = target_split[-2].upper()

        if target_doc_id in doc_cache:
            target_doc = doc_cache[target_doc_id]
            new_reference.set_target(target_doc)
            references.append(new_reference)

            cached_calls = cached_calls + 1
        else:
            incomplete_references.append((new_reference, target_doc_id))

            # If the document hasn't been cached, make an async request to make and cache it
            futures.append(session.get(base + '/api/v1/doc/docalias/?name=' + target_doc_id,
                                       background_callback=get_target_doc))

            uncached_calls = uncached_calls + 1

    # Now wait for all of async requests to complete, which should roughly be at the same time
    for future in futures:
        future.result()

    for reference in incomplete_references:
        target_doc_id = reference[1]
        reference[0].set_target(doc_cache[target_doc_id])
        references.append(reference[0])

    return references


def find_related_docs(G, root, level):

    if level == 0:
        return

    if root.id not in reference_cache.keys():
        print(root.id, "is not cached!")
        references = get_related_docs(root)

    else:
        print(root.id, "is cached!")
        references = reference_cache[root.id]

    for reference in references:
        if reference.source.id not in reference_cache.keys():
            reference_cache[reference.source.id] = [reference]

        elif reference not in reference_cache[reference.source.id]:
            reference_cache[reference.source.id].append(reference)

        add_reference_to_graph(G, reference)
        find_related_docs(G, reference.target, level - 1)


def draw_graph(G):
    labels = {}

    for node in G.nodes:
        labels[node] = node

    # pos = nx.spring_layout(G, k=0.2, iterations=20)
    pos = nx.shell_layout(G)
    # pos = nx.circular_layout(G)
    nx.draw_networkx_edges(G, pos, G.edges(), width=2, alpha=0.5, edge_color=nx.get_edge_attributes(G,'color').values())
    nx.draw_networkx_labels(G, pos, labels, node_size=50)
    plt.savefig('graph.png')
    plt.axis('off')
    plt.show()


def unpickle_caches():
    global doc_cache
    global reference_cache

    doc_cache_file = open('docs.pickle', 'rb')
    doc_cache = pickle.load(doc_cache_file)
    doc_cache_file.close()

    reference_cache_file = open('refs.pickle', 'rb')
    reference_cache = pickle.load(reference_cache_file)
    reference_cache_file.close()


def pickle_caches():
    global doc_cache
    global reference_cache

    doc_cache_file = open('docs.pickle', 'wb')
    pickle.dump(doc_cache, doc_cache_file, protocol=-1)
    doc_cache_file.close()

    reference_cache_file = open('refs.pickle', 'wb')
    pickle.dump(reference_cache, reference_cache_file, protocol=-1)
    reference_cache_file.close()


def main():
    G = nx.MultiGraph()

    unpickle_caches()

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

    pickle_caches()

    print('Drawing graph...')
    draw_graph(G)

main()

total_calls = cached_calls + uncached_calls
print("total calls: ", total_calls, " calls saved: ", cached_calls, " ", (cached_calls/max(total_calls, 1))*100, "%")

for key, ref_list in reference_cache.items():
    print("\nkey:", key)
    print("ref_list:")
    for ref in ref_list:
        print("   ", ref.source.id, "->", ref.target.id)
