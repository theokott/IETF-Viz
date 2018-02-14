# TODO:
#       CSS and HTML for styling and presentation!
#       Arrows showing relationships
#       Show future docs!
#       Handle the big spaces at the start and end of the tracks
#       Show drafts of the root doc
#       Make less calls for events! Do it once.

import requests as rq
import documents as docs
import drawing
from drawing import (rx, ry, x_buffer, y_buffer, track_height, track_title_length, area_title_length, date_y_offset,
                     date_x_offset, doc_height, colours, track_colours, scale_y_offset)
import _pickle as pickle
import svgwrite
import datetime
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import as_completed

base = 'https://datatracker.ietf.org'

# A dictionary of RFCs indexed on the id of the RFC (such as doc_cache['RFC1939'])
doc_cache = {}

# A dictionary of References indexed on the id of the source RFC
#   (such as reference_cache[ref.source.id] or reference_cache['RFC1939'])
reference_cache = {}

# A dictionary of groups indexed on their id (such as group_cache[1027])
group_cache = {}


def convert_string_to_datetime(string):
    date = string.split('T')[0]
    date_split = date.split('-')
    time = string.split('T')[1]
    time_split = time.split(':')

    return datetime.datetime(year=int(date_split[0]),
                             month=int(date_split[1]),
                             day=int(date_split[2]),
                             hour=int(time_split[0]),
                             minute=int(time_split[1]),
                             second=int(time_split[2]))


def get_doc_info(name):
    json = rq.get(base + '/api/v1/doc/document/' + name).json()

    update_doc = doc_cache[name]
    update_doc.set_draft_name(json['name'])
    update_doc.set_title(json['title'])
    update_doc.set_abstract(json['abstract'])
    update_doc.set_group_url(json['group'])
    update_doc.set_rfc_num(json['rfc'])

    if json['expires'] == None:
        today = datetime.datetime.today()
        update_doc.set_expiry_date(today)
    else:
        expiry_datetime = convert_string_to_datetime(json['expires'])
        update_doc.set_expiry_date(expiry_datetime)


def get_relationships(doc_name):
    relationships = []
    next = '/api/v1/doc/docevent/?limit=50&source=' + doc_name

    while next is not None:
        resp = rq.get(base + '/api/v1/doc/relateddocument/?limit=50&source=' + doc_name)
        json = resp.json()
        meta_data = json['meta']
        next = meta_data['next']

        relationships = relationships + resp.json().get('objects')



    return relationships


def build_group(group_id):
    json = rq.get(base + '/api/v1/group/group/' + str(group_id)).json()

    group_id = json['id']
    new_group = docs.Group(group_id)
    new_group.set_name(json['name'])
    new_group.set_parent_url(json['parent'])

    group_cache[group_id] = new_group


def get_group(group_id):
    if group_id in group_cache.keys():
        return group_cache[group_id]

    else:
        build_group(group_id)
        return group_cache[group_id]


def get_publish_event(name):
    events_json = rq.get(base + '/api/v1/doc/docevent/?limit=50&doc=' + doc_cache[name].draft_name).json()
    events = events_json['objects']

    for event in events:
        if event['type'] == 'published_rfc':
            return event

    return None


def get_revision_events(name):
    next = '/api/v1/doc/docevent/?limit=50&doc=' + doc_cache[name].draft_name
    revisions = []

    while next is not None:
        events_json = rq.get(base + next).json()
        meta_data = events_json['meta']
        next = meta_data['next']
        events = events_json['objects']

        for event in events:
            if event['type'] == 'new_revision':
                revisions.append(event)

    return revisions


# Some documents don't have "new_revision" types so the earliest possible event is used instead as the event
def get_earliest_event(name):
    next = '/api/v1/doc/docevent/?limit=50&doc=' + doc_cache[name].draft_name
    earliest_event = None

    while next is not None:
        events_json = rq.get(base + next).json()
        meta_data = events_json['meta']
        next = meta_data['next']
        events = events_json['objects']

        for event in events:
            if event['type'] == 'new_revision':
                earliest_event = event

    if earliest_event is None:
        return events[-1]
    else:
        return earliest_event


def build_doc_draft_name(name, alt_name=None):
    doc_cache[name] = docs.Document(name)
    get_doc_info(name)

    publish_event = get_publish_event(name)

    if publish_event is not None:
        publish_date = convert_string_to_datetime(publish_event['time'])
        doc_cache[name].set_publish_date(publish_date)

    for revision in get_revision_events(name):
        revision_datetime = convert_string_to_datetime(revision['time'])
        doc_cache[name].add_revision(revision_datetime)

    creation_event = get_earliest_event(name)
    creation_date = convert_string_to_datetime(creation_event['time'])
    doc_cache[name].set_creation_date(creation_date)

    # Create the group that the doc is part of
    group_url = doc_cache[name].group_url
    group_id = int(group_url.split('/')[-2])


    # Add the group's info to the doc's group fields
    doc_cache[name].set_group(get_group(group_id))
    doc_cache[name].set_area_url(group_cache[group_id].parent_url)

    # Add info for the doc's area/group's parent
    parent_url = group_cache[group_id].parent_url
    parent_id = int(parent_url.split('/')[-2])

    doc_cache[name].set_area(get_group(parent_id))

    if alt_name is not None:
        doc_cache[alt_name] = doc_cache[name]


def get_doc_alias(name):
    json = rq.get(base + '/api/v1/doc/docalias/' + name).json()
    doc_url = json['document']
    doc_alias = doc_url.split('/')[-2]

    return doc_alias


def get_doc(name):

    if name in doc_cache.keys():
        return doc_cache[name]

    else:
        alias = get_doc_alias(name)

        if alias in doc_cache.keys():
            doc_cache[name] = doc_cache[alias]
        else:
            build_doc_draft_name(alias, alt_name=name)

        return doc_cache[name]


def build_reference(reference, target_doc_name):
    get_doc(target_doc_name)
    reference.set_target(doc_cache[target_doc_name])

    return reference


def get_source_references(root):
    executor = ThreadPoolExecutor(max_workers=500)
    futures = []
    references = []

    relationships = get_relationships(root.draft_name)

    print(relationships)

    for relationship in relationships:
        new_reference = docs.Reference()
        new_reference.set_source(root)

        type_split = relationship.get('relationship').split('/')
        type = type_split[-2]
        new_reference.set_type(type)

        target_split = relationship.get('target').split('/')
        target_doc_name = target_split[-2].upper()

        futures.append(executor.submit(build_reference, new_reference, target_doc_name))

    for future in as_completed(futures):
        references.append(future.result())

    return references


def unpickle_caches():
    global doc_cache
    global reference_cache
    global group_cache

    try:

        doc_cache_file = open('docs.pickle', 'rb')
        doc_cache = pickle.load(doc_cache_file)
        doc_cache_file.close()
        print('Loaded document cache')

    except FileNotFoundError:
        print('No document cache found!')

    try:

        reference_cache_file = open('refs.pickle', 'rb')
        reference_cache = pickle.load(reference_cache_file)
        reference_cache_file.close()
        print('Loaded reference cache')

    except FileNotFoundError:
        print('No reference cache found!')

    try:

        group_cache_file = open('groups.pickle', 'rb')
        group_cache = pickle.load(group_cache_file)
        group_cache_file.close()
        print('Loaded group cache')

    except FileNotFoundError:
        print('No group cache found!')


def pickle_caches():
    global doc_cache
    global reference_cache

    doc_cache_file = open('docs.pickle', 'wb')
    pickle.dump(doc_cache, doc_cache_file, protocol=-1)
    doc_cache_file.close()
    print('Document cache written to disk!')

    reference_cache_file = open('refs.pickle', 'wb')
    pickle.dump(reference_cache, reference_cache_file, protocol=-1)
    reference_cache_file.close()
    print('Reference cache written to disk!')

    group_cache_file = open('groups.pickle', 'wb')
    pickle.dump(group_cache, group_cache_file, protocol=-1)
    group_cache_file.close()
    print('Group cache written to disk!')


def draw_areas(areas, dwg):
    y_offset = 0 + y_buffer
    area_count = 0

    for area in areas.values():
        track_colour = drawing.track_colours[area_count]
        y_title = y_offset + (area.height / 2)

        dwg.add(dwg.rect(
            insert=(x_buffer, y_offset), size=(area_title_length, area.height),
            fill=track_colour, stroke='#000000'))

        dwg.add(dwg.text(
            text=area.name, insert=(x_buffer + 10, y_offset + 10),
            textLength=[area_title_length], lengthAdjust='spacing',
            writing_mode='tb'
        ))

        area_count = area_count + 1
        y_offset = y_offset + area.height


def draw_tracks(areas, dwg, length):
    y_offset = 0 + y_buffer
    area_count = 0
    x = x_buffer + area_title_length
    track_length = length - track_title_length - area_title_length - (2 * x_buffer) + rx

    for area in areas.values():
        track_colour = drawing.track_colours[area_count]
        for group in area.groups.values():
            y_title = y_offset + 20

            dwg.add(dwg.rect(
                insert=(x,y_offset), size=(track_length, group.height), fill=track_colour, stroke='#000000'))

            dwg.add(dwg.text(
                text=group.name, insert=(x + 10, y_title),
                textLength=[track_height], lengthAdjust='spacing'))

            dwg.add(dwg.line(
                start=(x + rx + track_title_length, y_offset),
                end=(x + rx + track_title_length, y_offset + group.height),
                stroke='#000000', stroke_width=2
            ))

            y_offset = y_offset + group.height

        area_count = area_count + 1


def draw_docs(areas, dwg, start_date, timeline_length):
    area_count = 0
    y_offset = 0 + y_buffer
    doc_line_x = x_buffer + track_title_length + rx + area_title_length

    for area in areas.values():
        colour = drawing.colours[area_count]

        for group in area.groups.values():
            doc_num = 1

            for doc in group.documents:
                doc_x = (doc.document.creation_date - start_date).days\
                        + x_buffer + track_title_length + rx + area_title_length
                doc_y = y_offset + (doc_height * doc_num)
                text_x = doc_x
                name_text = doc.document.title
                revision_y = doc_y + doc_height/2

                if (doc.document.publish_date - doc.document.creation_date).days < 150:
                    doc_length = 150
                else:
                    doc_length = (doc.document.publish_date - doc.document.creation_date).days

                if doc.reference_type == 'refinfo':
                    width = 1
                    stroke_style = '10, 0'
                elif doc.reference_type == 'refnorm':
                    width = 4
                    stroke_style = '10, 0'
                elif doc.reference_type == 'root':
                    width = 10
                    stroke_style = '10, 0'
                else:
                    width = 4
                    stroke_style = '10, 5'

                # Draw the rectangle representing the doc
                dwg.add(dwg.rect(
                    insert=(doc_x, doc_y - doc_height), size=(doc_length, doc_height),fill=colour,
                    stroke='#000000', stroke_width=width, stroke_dasharray= stroke_style))

                # Draw the name of the doc
                dwg.add(dwg.text(
                    text=name_text, insert=(text_x, doc_y - doc_height/2), textLength=str(doc_length),
                    lengthAdjust='spacingAndGlyphs'
                ))

                dwg.add(dwg.line(
                    start=(doc_line_x, doc_y), end=(doc_line_x + timeline_length, doc_y), stroke='#111111',
                    stroke_width=1, stroke_opacity='0.3'
                ))

                for revision in doc.document.revision_dates:
                    revision_x = (revision - start_date).days + x_buffer + track_title_length + rx + area_title_length
                    print("REVISION", revision, revision_x, revision_y)
                    dwg.add(dwg.circle(
                        centre=(revision_x, revision_y), r=10, fill='#ffffff'
                    ))

                doc_num = doc_num + 1
            y_offset = y_offset + group.height
        area_count = area_count + 1


def draw_scale(dwg, start_date, end_date, areas_height):
    left_x = x_buffer + track_title_length + rx + area_title_length
    right_x = left_x + (end_date - start_date).days
    y = areas_height + y_buffer + scale_y_offset

    # Draw x axis
    dwg.add(dwg.line(
            start=(left_x, y), end=(right_x, y), stroke='#000000', stroke_width=2
            ))

    # Draw caps for axis
    dwg.add(dwg.line(
            start=(left_x, y+20), end=(left_x, y-20), stroke='#000000', stroke_width=2
            ))
    dwg.add(dwg.line(
        start=(right_x, y+20), end=(right_x, y-20), stroke='#000000', stroke_width=2
    ))

    # Draw dates at the end of each cap
    dwg.add(dwg.text(
        text=start_date, insert=(left_x - date_x_offset, y + date_y_offset)
    ))
    dwg.add(dwg.text(
        text=end_date, insert=(right_x - date_x_offset, y + date_y_offset)
    ))


def draw_axis_gridlines(dwg, start_date, end_date, areas_height):
    left_x = x_buffer + track_title_length + rx + area_title_length
    right_x = left_x + (end_date - start_date).days
    track_bottom_y = areas_height + y_buffer
    timeline_y = areas_height + y_buffer + scale_y_offset

    next_year = datetime.datetime(year=start_date.year + 1, month=1, day=1)
    time_delta = next_year - start_date

    gridline_x = left_x + time_delta.days

    while (end_date - next_year) > datetime.timedelta(days=0):
        # Draw grid line on tracks
        dwg.add(dwg.line(
            start=(gridline_x, track_bottom_y), end=(gridline_x, y_buffer), stroke='#111111', stroke_width=2, stroke_opacity='0.3'
        ))
        # Draw marker line on axis
        dwg.add(dwg.line(
            start=(gridline_x, timeline_y+10), end=(gridline_x, timeline_y-10), stroke='#000000', stroke_width=2
        ))
        # Draw date above timeline
        dwg.add(dwg.text(
            text=next_year, insert=(gridline_x - date_x_offset, timeline_y - date_y_offset)
        ))

        last_year = next_year
        next_year = datetime.datetime(year=next_year.year + 1, month=1, day=1)
        gridline_x = gridline_x + (next_year - last_year).days


def draw_timeline(areas, time_delta, start_date, end_date):
    img_length = time_delta.days + (2 * x_buffer) + (2 * rx) + track_title_length + area_title_length
    total_areas_height = 0

    for area in areas.values():
        total_areas_height = total_areas_height + area.height

    img_height = (y_buffer * 2) + total_areas_height + scale_y_offset

    dwg = svgwrite.Drawing(filename='timeline.svg', debug=False, size=(img_length, img_height))

    draw_areas(areas, dwg)
    draw_tracks(areas, dwg, img_length)
    draw_scale(dwg, start_date, end_date, total_areas_height)
    draw_axis_gridlines(dwg, start_date, end_date, total_areas_height)
    draw_docs(areas, dwg, start_date, time_delta.days)

    dwg.save()


def get_date(doc):
    return doc.publish_date


def filter_references(references):
    filter_lambda = (lambda x: x.type == 'refold' or
                               x.type == 'refinfo' or
                               x.type == 'refnorm' or
                               x.type == 'refunk'
                     )
    return list(filter(filter_lambda, references))


def generate_timeline(rfc_num):

    root = get_doc(rfc_num)

    print("root", root.id)

    references = get_source_references(root)

    for reference in references:
        print("id:", reference.target.id, "expiry:", reference.target.expiry_date)

    references.sort(key=(lambda x: x.target.expiry_date), reverse=True)
    references = filter_references(references)

    end_date = references[0].source.expiry_date
    start_date = references[-1].target.creation_date

    time_delta = end_date - start_date

    areas = {}

    for reference in references:
        new_document = drawing.DrawingDoc(reference.target, reference.type)
        if reference.target.area.name not in areas.keys():
            new_area = drawing.DrawingArea(reference.target.area.name)
            new_group = drawing.DrawingGroup(reference.target.group.name)
            new_group.add_document(new_document)
            new_area.add_group(new_group)
            areas[reference.target.area.name] = new_area

        else:
            if reference.target.group.name not in areas[reference.target.area.name].groups.keys():
                new_group = drawing.DrawingGroup(reference.target.group.name)
                new_group.add_document(new_document)
                areas[reference.target.area.name].add_group(new_group)
            else:
                areas[reference.target.area.name].groups[reference.target.group.name].add_document(new_document)

    root = references[0].source
    new_document = drawing.DrawingDoc(root, 'root')
    if root.area.name not in areas.keys():
        new_area = drawing.DrawingArea(root.area.name)
        new_group = drawing.DrawingGroup(root.group.name)
        new_group.add_document(new_document)
        new_area.add_group(new_group)
        areas[root.area.name] = new_area

    else:
        if root.group.name not in areas[root.area.name].groups.keys():
            new_group = drawing.DrawingGroup(root.group.name)
            new_group.add_document(new_document)
            areas[root.area.name].add_group(new_group)
        else:
            areas[root.area.name].groups[root.group.name].add_document(new_document)

    for area in areas.values():
        for group in area.groups.values():
            group.adjust_height()
        area.adjust_height()

    draw_timeline(areas, time_delta, start_date, end_date)


def main():
    rfc_num = 'rfc' + input('Enter the requested RFC number: ')
    root_doc = get_doc(rfc_num)
    doc_cache[root_doc.id] = root_doc

    generate_timeline(rfc_num)

unpickle_caches()
main()
pickle_caches()