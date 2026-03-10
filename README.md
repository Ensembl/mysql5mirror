# Ensembl MySQL v5.7 mirror

> Dockerised MySQL 5.7 server for hosting Ensembl genomic databases from releases 48 to 115.

This project is derived from [mysql4mirror](https://github.com/Ensembl/mysql4mirror) and uses the [official MySQL 5.7 Docker image](https://hub.docker.com/_/mysql) as its base.

## Prerequisites: Docker or a compatible runtime

These instructions use `docker` throughout, but any OCI-compatible container runtime will work. If you do not have Docker Desktop installed (or prefer not to use it), the following alternatives should work:

- **[Colima](https://github.com/abiosoft/colima)** -- a lightweight Docker-compatible runtime for macOS and Linux. Install with `brew install colima` and start with `colima start`. Once running, the `docker` CLI works as normal.
- **[Podman](https://podman.io/)** -- a daemonless container engine. Replace `docker` with `podman` in the commands below (or alias it: `alias docker=podman`).
- **[Rancher Desktop](https://rancherdesktop.io/)** -- provides `docker` CLI support

All commands below assume the `docker` CLI is available and connected to a running engine.

## Running the container with Docker

Specify the `MYSQL_ROOT_PASSWORD` environment variable and a volume for the datafiles when launching a new container:

```sh
export LOCAL_DB_DIR=/volume1/docker/mysql
export LOCAL_FLATFILES_DIR=/volume1/docker/flatfiles
export CONTAINER_NAME=mysql5mirror
export MYSQL_ROOT_PASSWORD=mysql5mirror
export TAG=latest
docker run --name ${CONTAINER_NAME} \
-e MYSQL_ROOT_PASSWORD=${MYSQL_ROOT_PASSWORD} \
-v ${LOCAL_DB_DIR}:/var/lib/mysql \
-v ${LOCAL_FLATFILES_DIR}:/flatfiles \
-p 35306:3306 \
--detach \
ensemblorg/mysql5mirror:${TAG}
```

This will run the container as a detached process, expose MySQL on your local machine on port `35306` (within the container this will remain `3306`), mount `/var/lib/mysql` on the container to your local data directory and mount `/flatfiles` to your local flatfiles directory. You can confirm the image has started by running `docker ps`. Only one MySQL user exists on the server `root` and is set to the password you gave the container during startup.

### Opening a shell into the container

```sh
docker exec -it $CONTAINER_NAME /bin/bash
```

Once in the container you will have access to the `ensembl_databases.py` and `load_mysql.sh` commands. This is the recommended way to use `load_mysql.sh`.

### Stopping the container

```sh
docker stop $CONTAINER_NAME
```

### Restarting the container

```sh
docker restart $CONTAINER_NAME
```

## Populating the running instance with Ensembl databases

### Getting databases from Ensembl

#### Using `ensembl_databases.py`

This container ships with a Python binary which can list, download and verify databases from releases 48 to 116. The library only uses core modules and is compatible with Python v3.2+. You can run it from within the container or from this repository. The binary can

- List the available databases
- Display information about the database
- Download the flat files
- Verify they are good

```sh
$ ./ensembl_databases.py --list '*core*49*homo*'
homo_sapiens_core_49_36k
$ ./ensembl_databases.py --download homo_sapiens_core_49_36k
Logging into ftp.ensembl.org
Listing database files for homo_sapiens_core_49_36k
Downloading ./homo_sapiens_core_49_36k/CHECKSUMS.gz
...
$ ./ensembl_databases.py --validate homo_sapiens_core_49_36k
All files are correct
```

The above command downloads the `homo_sapiens_core_49_36k` database to the local directory. You can use the `--basedir` flag to use a different location e.g. `/flatfiles` on the Docker container.

The binary takes as its final an unbounded list of database names or UNIX style glob strings (using `*` and `?` as wildcard characters).

**Be sure to quote your wildcard strings as command line shells will interpret this before `ensembl_databases.py` does.**

#### Manually downloading files

If you want to manually download the database dumps, then you can use our [FTP site using FTP or HTTP](https://www.ensembl.org/info/data/ftp/index.html), [rsync](https://www.ensembl.org/info/data/ftp/rsync.html) or even Globus through the "Shared EMBL-EBI public endpoint".

### Loading into MySQL

_The following commands assume you will be loading a database from flatfile dumps into a database._

#### Using `load_mysql.sh`

This container and repo ship with a bash script called `load_mysql.sh`. The script must be executed from within a working directory containing a database dump. The command will change its commands based on if it finds the `ENSEMBL_CONTAINER` environment variable. You can change the port used too by supplying a `MYSQL_PORT` environment variable.

**`load_mysql.sh` executes all commands in MySQL as the root user. The script responds to the `MYSQL_ROOT_PASSWORD` variable and will use this if ever defined.**

We recommend running `load_mysql.sh` from within a container (see instructions above about how to get a shell session into the executing container).

```sh
$ cd /flatfiles/homo_sapiens_core_49_36k
$ load_mysql.sh
!!!!!! Working with database homo_sapiens_core_49_36k

Working with table assembly
    Gunzipping assembly data from file assembly.txt.table.gz into assembly.txt ... Done
...

!!!!!! Database has been loaded
```

#### Manual loading

To manually load a database you must

- Create the database (N.B. the directory name does not always match the intended database name but the SQL file will)
- Load the Gzipped SQL file
- Load each table of data from the gzip'd flat files

```sh
cd homo_sapiens_core_49_36k
dbname=homo_sapiens_core_49_36k
mysql -e "create database ${dbname}"
gzip -dc ${dbname}.sql.gz | mysql $dbname
gzip -dc assembly.txt.table.gz > assembly.txt
mysqlimport $dbname assembly.txt
rm assembly.txt
```

The above commands can also be used from your local machine if you have access to the above binaries (`gzip` and `mysqlimport`) but the `mysqlimport` command needs the addition of `--local` to force it to copy the file to the database container automatically.

## Building the container

First generate the database lookup file (requires FTP access to ftp.ensembl.org):

```sh
python3 generate_dblookup.py
```

This will create `dblookup.json` covering releases 48-116. You can customise the range:

```sh
python3 generate_dblookup.py --start 48 --end 100
```

Then build the Docker image:

```sh
docker build -t ensemblorg/mysql5mirror .
```

## Container details

### Exposed Ports

```sh
# mysql
EXPOSE 3306
```

### Volumes

```sh
VOLUME /var/lib/mysql  # mysql datadir (managed by official image)
VOLUME /flatfiles      # Location of Ensembl flat file database dumps
```

### Environment variables used

```sh
MYSQL_ROOT_PASSWORD  mysql5mirror
TZ                   Europe/London
ENSEMBL_DBLOOKUP     /etc/dblookup.json
ENSEMBL_CONTAINER    true
MYSQL_ROOT_HOST      %
```

Root password will be bound to the wildcard `%` host to allow login from any network host.

## Testing status and support

Should you encounter a problem with running these scripts then [contact Ensembl helpdesk or our developers mailing list](https://www.ensembl.org/info/about/contact/index.html).
