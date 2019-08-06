from urllib.parse import quote_plus

from defusedxml import ElementTree
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from local.sql import Base, Url

 
SHORTCUTS = {
    'DuckDuckGo': '',
    'GitHub': 'gh'
}

class SearchEngine(Base):
    __tablename__ = 'search_engine'
    id = Column(Integer, primary_key=True)
    short_name = Column(String(16))
    long_name = Column(String(48))
    description = Column(String(1024))
    html_template = Column(String(2048))
    suggestion_template = Column(String(2048))
    icon = Column(String(4096))
    shortcut = Column(String(16))

    @classmethod
    def parse_odf(cls, db, content):
        root = ElementTree.fromstring(content)
        ns = root.tag[:-len('OpenSearchDescription')]

        short_name_elem = root.find(ns + 'ShortName')
        if short_name_elem is None:
            print('No ShortName defined')
            return

        short_name = short_name_elem.text
        se = db.query(SearchEngine).filter(SearchEngine.short_name == short_name).first()

        if se is None:
            se = SearchEngine(short_name=short_name)

        long_name = root.find(ns + 'LongName')
        if long_name is None:
            long_name = short_name
        else:
            long_name = long_name.text
        se.long_name = long_name
        se.description = root.find(ns + 'Description').text

        for elem in root.findall(ns + 'Url'):
            if elem.get('type') == 'text/html':
                se.html_template = elem.get('template')
            elif elem.get('type') == 'application/x-suggestions+json':
                se.suggestion_template = elem.get('template')
            
        for elem in root.findall(ns + 'Image'):
            if elem.get('height') != '16' or elem.get('width') != '16':
                continue
            se.icon = elem.text

        if not se.shortcut:
            se.shortcut = SHORTCUTS.get(short_name, '')

        db.add(se)
        db.commit()

    @classmethod
    def parse_file(cls, db, f):
        with open(f, 'r') as fd:
            buf = fd.read()

        cls.parse_odf(db, buf)


def search_redirect(request, query, search_id):
    search = query.get('q', [''])[0]
    search_engine = request.db.query(SearchEngine).get(search_id)

    location = search_engine.html_template.replace('{searchTerms}', quote_plus(search))
    request.send_response(302)
    request.send_header('Location', location)
    request.end_headers()
