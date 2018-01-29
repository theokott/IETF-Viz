# TODO:
#       NOT ALL DOCS HAVE RFC NUMBERS! NEED TO CACHE BASED ON NAME!
#       BCP and STDs do not have to consist of one doc, should be considered separate entities that are sometimes the
#           same as an RFC

import requests as rq
import networkx as nx
import matplotlib.pyplot as plt
import documents as doc
import drawing
from requests_futures.sessions import FuturesSession
import _pickle as pickle
import svgwrite
import datetime
from math import pi, sin, cos
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import as_completed
from svgwrite import cm, mm
# import graphviz
# import pydot as pd

base = 'https://datatracker.ietf.org'

# A dictionary of RFCs indexed on the id of the RFC (such as doc_cache['RFC1939'])
doc_cache = {}

# A dictionary of References indexed on the id of the source RFC
#   (such as reference_cache[ref.source.id] or reference_cache['RFC1939'])
reference_cache = {}

# A dictionary of groups indexed on their id (such as group_cache[1027])
group_cache = {}

session = FuturesSession(max_workers=50)


def get_group_info(sess, resp):
    json = resp.json()

    group_id = json["id"]

    new_group = doc.Group(group_id)
    new_group.set_name(json["name"])
    new_group.set_parent_url(json["parent"])

    group_cache[group_id] = new_group


def get_doc_info(sess, resp):
    json = resp.json()

    if json["rfc"] is None:
        doc_id = json["name"]

    else:
        doc_id = "RFC" + json["rfc"]

    updated_doc = doc_cache[doc_id]
    updated_doc.set_draft_name(json["name"])
    updated_doc.set_title(json["title"])
    updated_doc.set_abstract(json["abstract"])
    updated_doc.set_group_url(json["group"])


def resolve_doc_url(sess, resp):
    json = resp.json()
    doc_id = json['name'].upper()
    doc_url = json['document']

    # Sometimes a doc will be referred to in alternate ways such as BCP14 instead of RFC2119 so a link between the two
    #   is made for convenience
    if doc_id[0:3] != 'RFC':
        request = rq.get(base + doc_url)
        rfc_num = request.json()["rfc"]
        print("DOC ID", doc_id, "rfc_num", rfc_num, rfc_num is None)

        if rfc_num is None:
            new_doc = doc.RFC(doc_id)
            new_doc.set_draft_url(doc_url)

            doc_cache[new_doc.id] = new_doc
        else:
            alt_doc_id = doc_id
            print(alt_doc_id)
            new_doc_id = "RFC" + rfc_num
            new_doc = doc.RFC(new_doc_id)
            new_doc.set_draft_url(doc_url)

            doc_cache[new_doc.id] = new_doc
            doc_cache[alt_doc_id] = doc_cache[new_doc_id]
            print("Link made between:", new_doc_id, alt_doc_id)

    else:
        new_doc = doc.RFC(doc_id)
        new_doc.set_draft_url(doc_url)

        doc_cache[new_doc.id] = new_doc


def get_relationships(doc_name):
    resp = rq.get(base + '/api/v1/doc/relateddocument/?source=' + doc_name)
    relationships = resp.json().get('objects')

    return relationships


def build_group(group_id):
    # Create the group that the doc is part of
    group_url = "/api/v1/group/group/" + str(group_id)
    group_future = session.get(base + group_url, background_callback=get_group_info)
    group_future.result()

def get_group(group_id):
    if group_id in group_cache.keys():
        return group_cache[group_id]

    else:
        build_group(group_id)
        return group_cache[group_id]


def build_doc(rfc_num):
    # Resolve RFC number into URL that can be used to find out more info about the RFC
    url_future = session.get(base + '/api/v1/doc/docalias/' + rfc_num, background_callback=resolve_doc_url)
    url_future.result()

    # Get the info for the doc now that we have a URL to query
    doc_url = doc_cache[rfc_num].draft_url
    doc_future = session.get(base + doc_url, background_callback=get_doc_info)
    doc_future.result()


    # Get the date that the document was published
    events_json = rq.get(base + "/api/v1/doc/docevent/?doc=" + doc_cache[rfc_num].draft_name).json()
    events = events_json["objects"]
    for event in events:
        if event["type"] == "published_rfc":
            time_string = event["time"]
            date = time_string.split("T")[0]
            date_split = date.split("-")
            time = time_string.split("T")[1]
            time_split = time.split(":")

            publish_date = datetime.datetime(year=int(date_split[0]),
                                             month=int(date_split[1]),
                                             day=int(date_split[2]),
                                             hour=int(time_split[0]),
                                             minute=int(time_split[1]),
                                             second=int(time_split[2]))

            doc_cache[rfc_num].set_publish_date(publish_date)

    # Create the group that the doc is part of
    group_url = doc_cache[rfc_num].group_url
    group_id = int(group_url.split("/")[-2])

    # Add the group's info to the doc's group fields
    doc_cache[rfc_num].set_group(get_group(group_id))
    doc_cache[rfc_num].set_area_url(group_cache[group_id].parent_url)

    # Add info for the doc's area/group's parent
    parent_url = group_cache[group_id].parent_url
    parent_id = int(parent_url.split("/")[-2])

    doc_cache[rfc_num].set_area(get_group(parent_id))


def get_doc(rfc_num):

    if rfc_num in doc_cache.keys():
        return doc_cache[rfc_num]

    else:
        build_doc(rfc_num)
        print("BUILT", rfc_num)
        return doc_cache[rfc_num]


def add_reference_to_graph(G, reference):
    if reference.type == 'refold':
        G.add_edge(reference.source.id + " - " + reference.source.draft_name,
                   reference.target.id + " - " + reference.target.draft_name,
                   relType=reference.type, color='green', style='solid')
    else:
        G.add_edge(reference.source.id + " - " + reference.source.draft_name,
                   reference.target.id + " - " + reference.target.draft_name,
                   relType=reference.type, color='blue', style='solid')


# Wrap calls to build_doc in future for asynchronous
def get_source_references(root):
    incomplete_references = []
    executor = ThreadPoolExecutor(max_workers=500)
    futures = []
    references = []

    relationships = get_relationships(root.draft_name)

    for relationship in relationships:
        new_reference = doc.Reference()
        new_reference.set_source(root)

        type_split = relationship.get('relationship').split('/')
        new_reference.set_type(type_split[-2])

        target_split = relationship.get('target').split('/')
        target_doc_id = target_split[-2].upper()

        incomplete_references.append((new_reference, target_doc_id))
        futures.append(executor.submit(get_doc, target_doc_id))

    # Now wait for all of async requests to complete, which should roughly be at the same time
    for future in as_completed(futures):
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
        references = get_source_references(root)

    else:
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
    global group_cache

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

    try:

        group_cache_file = open('groups.pickle', 'rb')
        group_cache = pickle.load(group_cache_file)
        group_cache_file.close()
        print("Loaded group cache")

    except FileNotFoundError:
        print("No group cache found!")


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

    group_cache_file = open('groups.pickle', 'wb')
    pickle.dump(group_cache, group_cache_file, protocol=-1)
    group_cache_file.close()
    print("Group cache written to disk!")

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
def draw_timeline(timeline, img_size):

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

    dwg = svgwrite.Drawing(filename="obs-graph.svg", debug=False, size=(img_size, 500))

    dwg.add(dwg.line(start=(x_buffer + 2*rx, y0), end=(x0, y0), stroke='black', stroke_width=2))

    count = 0
    for doc in timeline:
        new_x = x0 - ((sep + (2 * rx)) * count)

        if count == 0:
            colour = '#5555ff'
        else:
            colour = '#bbbbff'

        dwg.add(dwg.ellipse(center=(new_x, y0), r=(rx, ry),
                            fill=colour, stroke='black', stroke_width=1))
        dwg.add(dwg.text(text=doc.id, insert=(new_x - rx/2, y0)))
        count = count + 1

        if count == len(timeline):
            old_x = new_x
            new_x = x0 - ((sep + (2 * rx)) * count)
            dwg.add(dwg.line(start=(new_x, y0 + 10), end=(new_x, y0 - 10), stroke='black', stroke_width=2))
            dwg.add(dwg.line(start=(new_x, y0), end=(old_x, y0), stroke='black', stroke_width=2))

    dwg.save()


def draw_timeline_areas(areas, time_delta, start_date, end_date):

    # Define constants for size of ellipses and edges
    rx = 90
    ry = 50
    track_height = 150
    x_buffer = rx + 20
    y_buffer = ry + 20
    length = time_delta.days + (2 * x_buffer) + rx

    num_of_groups = 1

    for area in areas.values():
        for group in area.groups.values():
            num_of_groups = num_of_groups + 1

    height = (y_buffer * 2) + (num_of_groups * 2 * ry) + (num_of_groups * track_height)

    # size of n ellipses + size of n-1 lines + buffer

    dwg = svgwrite.Drawing(filename="timeline.svg", debug=False, size=(length, height))

    # dwg.add(dwg.line(start=(x_buffer + 2*rx, y0), end=(x0, y0), stroke='black', stroke_width=2))

    area_count = 0
    y_offset = 0 + y_buffer
    for area in areas.values():
        group_count = 0
        colour = drawing.colours[area_count]
        track_colour = drawing.track_colours[area_count]
        for group in area.groups.values():
            dwg.add(dwg.rect(
                insert=(0,y_offset), size=(length, track_height), fill=track_colour, stroke='#000000'))

            dwg.add(dwg.text(
                text=group.name, insert=(0,y_offset + track_height/2), rotate=[90], textLength=[track_height]
            ))

            y = y_offset + y_buffer
            y_offset = y_offset + track_height

            for doc in group.references:
                x = (doc.target.publish_date - start_date).days + x_buffer + rx
                name_text = doc.target.publish_date

                dwg.add(dwg.ellipse(
                    center=(x, y), r=(rx, ry),fill=colour, stroke='#000000', stroke_width=1))
                dwg.add(dwg.text(text=name_text, insert=(x - rx / 2, y)))

        area_count = area_count + 1

    dwg.save()


def get_obs_docs(rfc_num):

    timeline = [doc_cache[rfc_num]]

    #   WHAT IF WE HAVEN'T ADDED THE REFENCES?
    for ref in get_source_references(get_doc(rfc_num)):
        if ref.type == "obs":
            timeline = timeline + get_obs_docs(ref.target.id)

    return timeline


def get_date(doc):
    return doc.publish_date


def filter_references(references):
    filter_lambda = (lambda x: x.type == "refold" or
                               x.type == "refinfo" or
                               x.type == "refnorm" or
                               x.type == "refunk"
                     )
    return list(filter(filter_lambda, references))


def generate_timeline(rfc_num):

    references = get_source_references(get_doc(rfc_num))
    references.sort(key=(lambda x: x.target.publish_date), reverse=True)
    references = filter_references(references)

    end_date = references[0].target.publish_date
    start_date = references[-1].target.publish_date

    time_delta = end_date - start_date
    print("TIME RANGE:", time_delta, references[0].target.publish_date, "-", references[-1].target.publish_date)

    docs = list(map(lambda x:x.target, references))

    areas = {}

    for reference in references:
        if reference.target.area.name not in areas.keys():
            new_area = drawing.DrawingArea(reference.target.area.name)
            new_group = drawing.DrawingGroup(reference.target.group.name)
            new_group.add_reference(reference)
            new_area.add_group(new_group)
            areas[reference.target.area.name] = new_area

        else:
            if reference.target.group.name not in areas[reference.target.area.name].groups.keys():
                new_group = drawing.DrawingGroup(reference.target.group.name)
                new_group.add_reference(reference)
                areas[reference.target.area.name].add_group(new_group)
            else:
                areas[reference.target.area.name]\
                    .groups[reference.target.group.name]\
                    .add_reference(reference)

    # for area in areas.keys():
    #     print("\nAREA:", area, areas[area].groups.keys())
    #     for group in areas[area].groups.keys():
    #         print("\tGROUP:", areas[area].groups[group].name)
    #         for doc in areas[area].groups[group].references:
    #             print("\t\tDOC", doc.target.draft_name)

    draw_timeline_areas(areas, time_delta, start_date, end_date)


    areas = {}
    groups = {}
    # for reference in references:
    #     print(reference.type == "obs" or reference.type == "refinfo" or reference.type == "refnorm" or reference.type == "refold" or reference.type == "refunk", reference.type)
    #     areas[reference.target.area.id] = reference.target.area
    #     groups[reference.target.group.id] = reference.target.group
    #     print(reference.target.area.name, reference.target.group.name)

    draft_timeline = get_obs_docs(rfc_num)
    draft_timeline.sort(key=get_date, reverse=True)


def main():
    G = nx.MultiDiGraph()


    rfc_num = 'RFC' + input('Enter the requested RFC number: ')

    # deg_of_separation = input('Enter the degree of separation: ')

    root_doc = get_doc(rfc_num)

    # G.add_node(root_doc)
    doc_cache[root_doc.id] = root_doc

    # find_related_docs(G, root_doc, int(deg_of_separation))

    # print('Drawing graph...')
    # draw_graph(G)
    # nx.drawing.nx_pydot.write_dot(G, 'graph.dot')

    generate_timeline(rfc_num)

    # draw_circle_graph(rfc_num)

unpickle_caches()
main()
pickle_caches()