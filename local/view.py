from datetime import datetime
import enum
import json

from sqlalchemy import desc
from sqlalchemy.inspection import inspect


def serialize(request, cls, obj_id, level):
    obj_id = int(obj_id)
    obj = request.db.query(cls).filter(cls.id == obj_id).one()

    r = {}
    for col in cls.__table__.columns:
        val = getattr(obj, col.name)
        if isinstance(val, datetime):
            val = datetime.timestamp(val)
        elif isinstance(val, enum.Enum):
            val = val.name
        r[col.name] = val

    # Nest serialize relationship
    if level > 0:
        level -= 1
        for key, val in inspect(cls).relationships.items():
            rel_id_attr = list(val.local_columns)[0].name
            rel_id = getattr(obj, rel_id_attr)
            r[key] = serialize(request, val.argument, rel_id, level)

    return r


def api_detail_view(cls, level, request, query, obj_id):
    r = serialize(request, cls, obj_id, level)
    r = json.dumps(r).encode('ascii')
    request.send_content_response(r, 'application/json')


def list_serialize(request, cls, _filter, level):
    objs = request.db.query(cls).filter_by(**_filter)

    order = 'id'
    if hasattr(cls, 'date'):
        order = 'date'

    order = getattr(cls, order)
    objs = objs.order_by(desc(order))
    objs = objs.limit(30)

    r = {
        'count': objs.count(),
        'objs': []
    }

    for obj in objs:
        r['objs'].append(serialize(request, cls, obj.id, level))

    return r


def api_list_view(cls, level, request, query):
    r = list_serialize(request, cls, {}, level)
    r = json.dumps(r).encode('ascii')
    request.send_content_response(r, 'application/json')
