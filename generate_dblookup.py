#!/usr/bin/env python3

"""
.. See the NOTICE file distributed with this work for additional information
   regarding copyright ownership.

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.

   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
"""

import ftplib
import json
import argparse
import sys
import time

SERVER = "ftp.ensembl.org"
DEFAULT_START = 48
DEFAULT_END = 116


def list_databases_for_release(ftp, release):
    """List all database directories under /pub/release-{N}/mysql/"""
    mysql_path = "/pub/release-{}/mysql".format(release)
    try:
        entries = ftp.nlst(mysql_path)
    except ftplib.error_perm:
        print("  Warning: Could not list {}".format(mysql_path), file=sys.stderr)
        return []

    databases = []
    for entry in entries:
        # nlst returns full paths, extract the directory name
        dbname = entry.rsplit("/", 1)[-1]
        # Skip non-database entries (files like CHECKSUMS.gz, README, or hidden entries)
        if not dbname or dbname.startswith(".") or "." in dbname or dbname.isupper():
            continue
        databases.append({
            "database": dbname,
            "path": "{}/{}".format(mysql_path, dbname),
            "server": SERVER,
        })
    return databases


def main():
    parser = argparse.ArgumentParser(
        description="Generate dblookup.json by crawling the Ensembl FTP server"
    )
    parser.add_argument(
        "--start",
        type=int,
        default=DEFAULT_START,
        help="First release number (default: {})".format(DEFAULT_START),
    )
    parser.add_argument(
        "--end",
        type=int,
        default=DEFAULT_END,
        help="Last release number (default: {})".format(DEFAULT_END),
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        default="dblookup.json",
        help="Output file (default: dblookup.json)",
    )
    args = parser.parse_args()

    lookup = {}

    print("Connecting to {}...".format(SERVER))
    ftp = ftplib.FTP()
    ftp.connect(SERVER)
    ftp.login()

    for release in range(args.start, args.end + 1):
        print("Processing release {}...".format(release))
        databases = list_databases_for_release(ftp, release)
        for db in databases:
            lookup[db["database"]] = db
        print("  Found {} databases".format(len(databases)))
        # Brief pause to be polite to the FTP server
        time.sleep(0.5)

    ftp.quit()
    ftp.close()

    print("Writing {} databases to {}".format(len(lookup), args.output))
    with open(args.output, "w") as f:
        json.dump(lookup, f, indent=2, sort_keys=True)

    print("Done.")


if __name__ == "__main__":
    main()
