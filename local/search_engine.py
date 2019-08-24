import re
import urllib.parse

from defusedxml import ElementTree
import yaml
from sqlalchemy import Boolean, Column, Integer, String
from sqlalchemy.orm import relationship

from local.sql import Base, Url


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
    store_results = Column(Boolean(), default=True)

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

        se.shortcut = short_name.lower()

        db.add(se)
        db.commit()

    @classmethod
    def parse_xml_file(cls, db, f):
        with open(f, 'r') as fd:
            buf = fd.read()

        cls.parse_odf(db, buf)

    @classmethod
    def parse_yaml_file(cls, db, f):
        f = yaml.load(open(f, 'r').read(), Loader=yaml.SafeLoader)
        if not f.get('long_name'):
            f['long_name'] = f['short_name']

        se = db.query(SearchEngine).filter(SearchEngine.short_name == f['short_name']).first()
        if se:
            for key, val in f.items():
                setattr(se, key, val)
        else:
            se = SearchEngine(**f)

        db.add(se)
        db.commit()

    @classmethod
    def _get_search_terms(cls, se, url, in_url):
        print('term matching %s vs %s' % (se, url))
        terms_re = re.escape(se)

        if in_url:
            replace_by = '([^/]*)'
        else:
            replace_by = '.*'
        terms_re = terms_re.replace('\\{searchTerms\\}', replace_by)

        print('check re %s / %s' % (terms_re, url))
        m = re.search(terms_re, url)

        if m is None:
            return None

        return m.group(0)

    @classmethod
    def get_from_url(cls, db, url):
        if url is None:
            return
        parsed_url = urllib.parse.urlsplit(url)
        url_params = urllib.parse.parse_qs(parsed_url.query)

        print('checking url %s for searhc' %url)
        for se in db.query(SearchEngine).all():
            print('against %s' % se.html_template)
            se_url = urllib.parse.urlsplit(se.html_template)

            if se_url.scheme != parsed_url.scheme or se_url.netloc != parsed_url.netloc:
                print('scheme or netloc not matching for %s' % se.html_template)
                continue

            # Match the url
            if '{searchTerms}' in se_url.path:
                path = urllib.parse.unquote_plus(url)
                terms = cls._get_search_terms(se_url.path, path, True)

                if terms is None:
                    print('search term in url not matched (se %s)' % se.html_template)
                    continue
                print('found search %s on %s' % (terms, se.html_template))
                return se, terms
            else:
                if se_url.path != parsed_url.path:
                    print('se %s path did not match' % se.html_template)
                    continue

            # Path matched, find search term in params
            se_params = urllib.parse.parse_qs(se_url.query)
            terms = None
            for key, val in se_params.items():
                val = val[0]
                if '{searchTerms}' in val:
                    if key not in url_params:
                        print('param %s for se %s missing' % (key, se.html_template))
                        break
                    terms = cls._get_search_terms(val, url_params[key][0], False)

                    if terms is None:
                        print('no param %s match for se %s' % (key, se.html_template))
                        break
                else:
                    if url_params.get(key) != val:
                        print('non matching param %s = %s for se %s (%s = %s)' % (key, url_params.get(key), se.html_template, key, val))
                        break
            else:
                print('matching se %s, search terms: %s' % (se.html_template, terms))
                return se, terms

            print('no se match')
            return None

    def get_search_url(self, query):
        se_url = urllib.parse.urlsplit(self.html_template)

        if '{searchTerms}' in se_url.path:
            query = urllib.parse.quote_plus(query)
            se_url_path = se_url.path.replace('{searchTerms}', query)
            se_url = se_url._replace(path=se_url_path)
            return urllib.parse.urlunsplit(se_url)

        se_params = urllib.parse.parse_qs(se_url.query)
        for key, val in se_params.items():
            val = val[0]
            if '{searchTerms}' in val:
                se_params[key] = val.replace('{searchTerms}', query)
                break
        else:
            raise Exception('could not find {searchTerms} parameter')

        se_url_query = urllib.parse.urlencode(se_params)
        se_url = se_url._replace(query=se_url_query)
        return urllib.parse.urlunsplit(se_url)


def search_redirect(request, query, search_id):
    search = query.get('q', [''])[0]
    search_engine = request.db.query(SearchEngine).get(search_id)

    location = search_engine.get_search_url(search)
    request.send_response(302)
    request.send_header('Location', location)
    request.end_headers()

    from local.searchs import Search
    s = Search.get_or_create(request.db, search, search_engine)
    request.db.add(s)
    request.db.commit()
