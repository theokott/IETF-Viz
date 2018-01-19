# TODO:
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
#       Need to edit generated Dot/Graphviz files to improve layout
#           - Ranksep
#           - Clusters? 

import requests as rq
import networkx as nx
import matplotlib.pyplot as plt
import documents as doc
from requests_futures.sessions import FuturesSession
import _pickle as pickle
import svgwrite
from os.path import isfile
from math import pi, sin, cos
from svgwrite import cm, mm
# import graphviz
# import pydot as pd

base = 'https://datatracker.ietf.org'

# A dictionary of RFCs indexed on the id of the RFC (such as doc_cache['RFC1939'])
doc_cache = {}

# A dictionary of References indexed on the id of the source RFC
#   (such as reference_cache[ref.source.id] or reference_cache['RFC1939'])
reference_cache = {}
cached_calls = 0
uncached_calls = 0
session = FuturesSession(max_workers=50)


# Actually build the target doc here!
# Could either have hashtable of useful WGs or add them dynamically (would require ANOTHER async call)
def build_target_doc(sess, resp):
    print("build_target_doc resp: ", resp.json()["name"])

    return True


# TODO: REWRITE THIS TO MAKE A PROPER CALL TO /doc/document/[docname]/
def get_target_doc(sess, resp):

    # N.B. the data stored in the field 'name' in the JSON is actually the RFC Number and thus a unique ID.
    # The name of the draft that became the RFC is contained within the URL. This can be identical to the RFC Number

    body = resp.json().get('objects')[0]
    doc_id = body.get('name').upper()
    doc_url = body.get('document')
    split_url = doc_url.split('/')
    doc_name = split_url[-2]

    print("CALLING /api/v1/doc/document/" +  doc_name)
    session.get(base + "/api/v1/doc/document/" + doc_name, background_callback=build_target_doc).result()

    new_doc = doc.RFC(doc_id)
    new_doc.set_draft_url(doc_url)
    new_doc.set_draft_name(doc_name)

    doc_cache[new_doc.id] = new_doc

# REWRITE THIS!
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
        # new_doc = doc.RFC(rfc_num)
        # new_doc.set_draft_url(get_doc_url(new_doc.id))
        # new_doc.set_draft_name(get_name(new_doc.draft_url))
        #
        # return new_doc

        future = session.get(base + '/api/v1/doc/docalias/?name=' + rfc_num, background_callback=get_target_doc)
        future.result()

        return doc_cache[rfc_num]


def add_reference_to_graph(G, reference):
    if reference.type == 'refold':
        G.add_edge(reference.source.id, reference.target.id, relType=reference.type, color='green', style='solid')
    else:
        G.add_edge(reference.source.id, reference.target.id, relType=reference.type, color='blue', style='solid')


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
            print(target_doc_id, "is in the cache")
            target_doc = doc_cache[target_doc_id]
            new_reference.set_target(target_doc)
            references.append(new_reference)

            cached_calls = cached_calls + 1
        else:
            incomplete_references.append((new_reference, target_doc_id))
            print(target_doc_id, "is not in the cache")

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
        print(root.id, "refs are not cached!")
        references = get_related_docs(root)

    else:
        print(root.id, "refs are cached!")
        references = reference_cache[root.id]

    if len(references) == 0:
        reference_cache[root.id] = []

    else:
        for reference in references:
            if root.id not in reference_cache.keys():
                reference_cache[root.id] = [reference]

            elif reference not in reference_cache[root.id]:
                reference_cache[root.id].append(reference)

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

    try:

        doc_cache_file = open('docs.pickle', 'rb')
        doc_cache = pickle.load(doc_cache_file)
        doc_cache_file.close()
        print("Loaded document cache")

    except FileNotFoundError:
        print("No document cache found!")

    try:

        reference_cache_file = open('refs.pickle', 'rb')
        reference_cache = pickle.load(reference_cache_file)
        reference_cache_file.close()
        print("Loaded reference cache")

    except FileNotFoundError:
        print("No reference cache found!")


def pickle_caches():
    global doc_cache
    global reference_cache

    doc_cache_file = open('docs.pickle', 'wb')
    pickle.dump(doc_cache, doc_cache_file, protocol=-1)
    doc_cache_file.close()
    print("Document cache written to disk!")

    reference_cache_file = open('refs.pickle', 'wb')
    pickle.dump(reference_cache, reference_cache_file, protocol=-1)
    reference_cache_file.close()
    print("Reference cache written to disk!")

def draw_circle_graph(rfc_num):
    og = nx.MultiDiGraph()
    obs_refs = []

    refs = reference_cache[rfc_num]
    num_of_refs = len(refs)
    angle_incr = pi*(2/num_of_refs)
    radius = 30
    buffer = radius * 1.1
    x0 = 300
    y0 = 300
    count = 0

    dwg = svgwrite.Drawing(filename="obs-graph.svg", debug=True)
    for ref in refs:
        new_x = x0 * sin(angle_incr * count) + (x0 + buffer * 3)
        new_y = y0 * cos(angle_incr * count) + (y0 + buffer)
        id = str(ref.target.id)

        print("new x: ", new_x)
        print("new y: ", new_y)

        dwg.add(dwg.line(start=(new_x, new_y), end=(x0 + (buffer * 3), y0 + buffer), stroke='black', stroke_width=2))
        dwg.add(dwg.ellipse(center=(new_x, new_y), r=(radius*3, radius),
                            fill='#7777ff', stroke='black', stroke_width=1))
        dwg.add(dwg.text(text=id, insert=(new_x - (radius * 3/4), new_y)))

        count = count + 1

    dwg.add(dwg.ellipse(center=(x0 + (buffer * 3), y0 + buffer), r=(radius*3, radius),
                       fill='blue', stroke='black', stroke_width=1))
    dwg.save()


# Encode status (is it a draft?)
# Scale position based on date
# Split into smaller functions
def draw_timeline(timeline):

    # Define constants for size of ellipses and edges
    rx = 90
    ry = 50
    sep = 70
    x_buffer = rx + 20
    y_buffer = ry + 20
    size = len(timeline)

    # size of n ellipses + size of n-1 lines + buffer
    x0 = (size * 2 * rx) + ((size - 1) * sep) + x_buffer
    y0 = ry + y_buffer

    dwg = svgwrite.Drawing(filename="obs-graph.svg", debug=True)

    dwg.add(dwg.line(start=(x_buffer + 2*rx, y0), end=(x0, y0), stroke='black', stroke_width=2))

    count = 0
    for doc in timeline:
        print(doc)
        new_x = x0 - ((sep + (2 * rx)) * count)

        if doc is None:
            dwg.add(dwg.line(start=(new_x, y0 + 10), end=(new_x, y0 - 10), stroke='black', stroke_width=2))
        else:
            dwg.add(dwg.ellipse(center=(new_x, y0), r=(rx, ry),
                                fill='#bbbbff', stroke='black', stroke_width=1))
            dwg.add(dwg.text(text=doc.id, insert=(new_x - rx/2, y0)))
        count = count + 1

    dwg.save()


def get_obs_docs(rfc_num):

    timeline = [doc_cache[rfc_num]]

    is_end = True


    #   WHAT IF WE HAVEN'T ADDED THE REFENCES?
    for ref in reference_cache[rfc_num]:
        if ref.type == "obs":
            is_end = False
            timeline = timeline + get_obs_docs(ref.target.id)

    if is_end:
        return timeline + [None]
    else:
        return timeline



def draw_svg(name):
    dwg = svgwrite.Drawing('test.svg', profile='tiny')
    dwg.add(dwg.line((0, 0), (10, 0), stroke=svgwrite.rgb(10, 10, 16, '%')))
    dwg.add(dwg.text('Test', insert=(0, 0.2)))
    dwg.save()


def main():
    G = nx.MultiDiGraph()

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

    # pickle_caches()

    print('Drawing graph...')
    draw_graph(G)
    nx.drawing.nx_pydot.write_dot(G, 'graph.dot')

    # timeline = get_obs_docs(rfc_num)

    # draw_timeline(timeline)
    # draw_circle_graph(rfc_num)

main()

total_calls = cached_calls + uncached_calls
print("total calls: ", total_calls, " calls saved: ", cached_calls, " ", (cached_calls/max(total_calls, 1))*100, "%")
