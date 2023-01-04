DLProxy is an experimental SSL intercepting proxy initially based on https://github.com/inaz2/proxy2/

Its main features are:
- Download interception: file downloads can be stored on the proxy
- Search history: search keywords are extracted from search engines url and browser search resulted are linked to them
- Browsing history: the browsing history can be viewed and searched, in a chronological view and in a graph view

Installation, on Debian Buster:

> apt install -y virtualenv build-essential python3-dev libpq-dev libmagic1 postgresql npm
>
> virtualenv venv
> source venv/bin/activate
> pip install -r requirements.txt
>
> echo "host all  all    127.0.0.1/32  md5" >> /etc/postgresql/13/main/pg_hba.conf
> echo "listen_addresses='127.0.0.1'" >> /etc/postgresql/13/main/postgresql.conf
> systemctl restart postgresql
> su postgres -c "psql --command \"CREATE USER dlproxy WITH SUPERUSER PASSWORD 'dlproxy';\""
> su postgres -c "psql --command \"CREATE DATABASE dlproxy OWNER dlproxy;\""
>
> cd dlui
> npm install -g @angular/cli@8
> npm install
> ng build
>
> python3 dlproxy.py --init-db
> mkdir cache certs downloads

Copy the conf and edit it:

> mkdir /etc/dlproxy
> cp dlproxy.conf /etc/dlproxy

The proxy can then be run with:

> python3 dlproxy.py
