from datetime import datetime
import enum
import json

from sqlalchemy import desc, DateTime, Integer
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
            if rel_id is None:
                r[key] = None
            else:
                r[key] = serialize(request, val.argument, rel_id, level)

    return r


def api_detail_view(cls, level, request, query, obj_id):
    r = serialize(request, cls, obj_id, level)
    r = json.dumps(r).encode('ascii')
    request.send_content_response(r, 'application/json')


OPERATORS = ('eq', 'gt', 'gte', 'lt', 'lte', 'ilike')


def op_func(op, a, b):
    OP = {
        'eq': '=',
        'gt': '>',
        'gte': '>=',
        'lt': '<',
        'lte': '<=',
        'ilike': 'ilike'
    }
    if op not in OPERATORS:
        raise Exception('Operator "%s" not supported' % op)
    op = OP[op]

    if op == 'ilike':
        b = b.replace('\\', '\\\\')
        b = b.replace('%', '\\%')
        b = b.replace('_', '\\_')
        b = '%' + b + '%'

    return a.op(op)(b)


def convert_value(cls, attr, val):
    columns = inspect(cls).columns
    col_type = getattr(columns, attr).type
    if isinstance(col_type, DateTime):
        return datetime.fromtimestamp(int(val))
    elif isinstance(col_type, Integer):
        return int(val)
    return val


def list_serialize(request, query, cls, level, limit=30):
    # Ordering
    order = 'id'
    descending = True

    if hasattr(cls, 'date'):
        order = 'date'

    if query.get('order'):
        descending = False
        order = query['order'][0]
        if order.startswith('-'):
            descending = True
            order = order[1:]

    if hasattr(cls, order):
        order = getattr(cls, order)

        if descending:
            order = desc(order)
    else:
        order = None

    # Filtering
    filters = []
    for key, vals in query.items():
        if not key.startswith('f_'):
            continue

        key = key[2:]
        op = 'eq'

        for val in vals:
            if '__' in key:
                # Build query to filter on relationship, like:
                # db.query(UrlAccess).filter(UrlAccess.url.has(Url.id == 1))

                attr, subattr = key.split('__', 1)

                if subattr in OPERATORS:
                    val = convert_value(cls, attr, val)
                    filters.append(op_func(subattr, getattr(cls, attr), val))
                    print('added filter %s %s %s' % (attr, subattr, val))
                    continue

                op = 'eq'
                if '__' in subattr:
                    subattr, op = subattr.rsplit('__', 1)

                rel = getattr(cls, attr, None)
                rel_cls = inspect(cls).relationships[attr].argument
                rel_attr = getattr(rel_cls, subattr, None)

                if rel is None or rel_attr is None:
                    continue

                print('added filter %s->%s %s %s' % (attr, subattr, op, val))
                has = rel.has(op_func(op, rel_attr, val))
                filters.append(has)
            elif hasattr(cls, key):
                filters.append(op_func('eq', getattr(cls, key), val))

    print('filter %s' % filters)
    objs = request.db.query(cls).filter(*filters)
    count = objs.count()

    if order is not None:
        objs = objs.order_by(order)

    if 'offset' in query:
        offset = int(query['offset'][0])
        objs = objs.offset(offset)
    else:
        offset = 0


    if 'limit' in query:
        limit = int(query['limit'][0])
        if limit >= 1000:
            limit = 1000

    if limit is not None:
        objs = objs.limit(limit)

    r = {
        'count': count,
        'offset': offset,
        'objs': []
    }

    for obj in objs:
        r['objs'].append(serialize(request, cls, obj.id, level))

    return r


def api_list_view(cls, level, request, query):
    r = list_serialize(request, query, cls, level)
    r = json.dumps(r).encode('ascii')
    request.send_content_response(r, 'application/json')
