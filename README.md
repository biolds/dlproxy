Proxy based on https://github.com/inaz2/proxy2/

On buster:
apt install -y virtualenv build-essential python3-dev libpq-dev libmagic1 postgresql npm

virtualenv venv
source venv/bin/activate
pip install -r requirements.txt

echo "host all  all    127.0.0.1/32  md5" >> /etc/postgresql/13/main/pg_hba.conf
echo "listen_addresses='127.0.0.1'" >> /etc/postgresql/13/main/postgresql.conf
systemctl restart postgresql
su postgres -c "psql --command \"CREATE USER dlproxy WITH SUPERUSER PASSWORD 'dlproxy';\""
su postgres -c "psql --command \"CREATE DATABASE dlproxy OWNER dlproxy;\""

cd dlui
npm install -g @angular/cli@8
npm install
ng build
