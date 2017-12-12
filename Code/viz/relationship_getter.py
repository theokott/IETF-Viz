import requests as rq
import asyncio
from aiohttp import web
from aiohttp import ClientSession

base = 'https://datatracker.ietf.org'
loop = asyncio.get_event_loop()
session = ClientSession()

def get_relationships(doc_name):
    resp = rq.get(base + '/api/v1/doc/relateddocument/?source=' + doc_name)
    relationships = resp.json().get('objects')

    return relationships

async def get_doc(rfc_num):
    session.get(base + '/api/v1/doc/docalias/?name=' + rfc_num)

    resp = rq.get(base + '/api/v1/doc/docalias/?name=' + rfc_num)
    body = resp.json().get('objects')[0]

    return body.get('document')

relationships = get_relationships('draft-myers-pop-pop3')

for relationship in relationships:
    target_split = relationship.get('target').split('/')
    target_doc_id = target_split[-2].upper()

    print(target_doc_id, " is not cached")
    target_doc = get_doc(target_doc_id)
