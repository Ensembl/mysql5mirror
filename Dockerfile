#
# Derived from the mysql4mirror project (https://github.com/Ensembl/mysql4mirror)
#

FROM mysql:5.7.44
LABEL maintainer="helpdesk@ensembl.org"

#env
ENV TZ=Europe/London
ENV ENSEMBL_CONTAINER='true'
ENV ENSEMBL_DBLOOKUP=/etc/dblookup.json

# Allow root login from any host (the official image respects this)
ENV MYSQL_ROOT_HOST='%'

# Install python3 for ensembl_databases.py
RUN apt-get update && apt-get install -q -y python3 && rm -rf /var/lib/apt/lists/*

# Add Ensembl scripts
COPY ensembl_databases.py /bin/.
RUN chmod ugo+x /bin/ensembl_databases.py
COPY load_mysql.sh /bin/.
RUN chmod ugo+x /bin/load_mysql.sh
COPY dblookup.json /etc/.

# Volume for flat file database dumps
VOLUME /flatfiles
