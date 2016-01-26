# https://pythonhosted.org/setuptools/setuptools.html#namespace-packages
__import__('pkg_resources').declare_namespace(__name__)

import os
import sys
import logging
import subprocess
import shutil
import datetime
import csv

import ConfigParser

from boto.s3.connection import S3Connection
from boto.s3.key import Key

"""
Things this takes for granted:

* That your source directory has (at least) two children: data and meta
* That data and meta are where you store raw GeoJSON files and CSV "meta" files respectively
* That meta files are named "wof-SOMETHING-latest.csv"

"""

class bundler:

    def __init__ (self, **kwargs):

        source = kwargs.get('source', None)

        if not source:
            raise Exception, "source is not defined"

        self.source = os.path.abspath(source)

        if not os.path.exists(self.source):
            raise Exception, "%s does not exist" % self.source

        self.data = os.path.join(self.source, 'data')
        self.meta = os.path.join(self.source, 'meta')
        
        #

        dest = kwargs.get('dest', None)

        if not source:
            raise Exception, "dest is not defined"

        self.dest = os.path.abspath(kwargs.get('dest', None))

        #

        clone = kwargs.get('clone', None)

        if not clone:
            raise Exception, "clone is not defined"

        self.clone = os.path.abspath(clone)

        if not os.path.exists(self.clone):
            raise Exception, "%s does not exist" % self.clone
            
        #

        aws_bucket = kwargs.get('aws_bucket', None)

        if not aws_bucket:
            raise Exception, "aws_bucket not defined"

        aws_creds = kwargs.get('aws_creds', None)

        if aws_creds:

            aws_creds = os.path.abspath(aws_creds)

            if not os.path.exists(aws_creds):
                raise Exception, "%s does not exist" % aws_creds

            cfg = ConfigParser.ConfigParser()
            cfg.read(aws_creds)

            aws_key = cfg.get('default', 'aws_access_key_id')
            aws_secret = cfg.get('default', 'aws_secret_access_key')
        
            conn = S3Connection(aws_key, aws_secret)
        else:
            conn = S3Connection()

        bucket = conn.get_bucket(aws_bucket)

        self.conn = conn
        self.bucket = bucket

        #

        self.force = kwargs.get('force', False)

    def bundle(self, name):

        bundle = "wof-%s-bundle" % name

        root = os.path.join(self.dest, bundle)
        dest = os.path.join(root, "data")

        source = "file://%s" % self.data

        csv_fname = "wof-%s-latest.csv" % name
        csv_latest = os.path.join(self.meta, csv_fname)

        csv_local = os.path.join(root, csv_fname)
        csv_sha1 = "%s.sha1.txt" % csv_latest

        tarball = "%s.tar.bz2" % root
        tarball_sha1 = "%s.sha1.txt" % tarball

        readme = os.path.join(self.dest, "wof-%s-bundle.txt" % name)

        # do we need to do any work? like has anything changed?
        # we will use the SHA1 hash of the CSV files to test that
        # since the SHA1 hash of the tarball seems to change between
        # runs (20160118/thisisaaronland)

        if self.bucket and not self.force:

            # It is unclear to me whether this is a constraint we
            # actually want to impose (20160119/thisisaaronland)

            """
            fh = open(csv_latest)
            reader = csv.DictReader(fh)

            try:
                reader.next()
            except StopIteration, e:
                logging.info("%s has no records, skipping" % csv_latest)
                return True
            except Exception, e:
                logging.error("failed to parse %s, because %s" % (csv_latest, e))
            """

            local_hash = self.hash_file(csv_latest)
            remote_hash = self.read_remote(csv_sha1)
            
            if local_hash == remote_hash :
                logging.info("nothing has changed, skipping %s" % bundle)
                return True
            
        # okay, we need to do something - first some general house-keeping

        dirs = (root,)
        files = (tarball, tarball_sha1, csv_sha1, readme)	# note the absense of csv_local which is copied in to root

        self.cleanup(dirs, files)

        if not os.path.exists(dest):
            logging.info("mkdir %s" % dest)
            os.makedirs(dest)

        # bundle the files

        cmd = [ self.clone, "-source", source, "-dest", dest, csv_latest ]
        logging.info(cmd)

        subprocess.check_call(cmd)

        # now include the meta files

        shutil.copy(csv_latest, csv_local)
        
        # now make a tarball

        cmd = ["tar", "-C", self.dest, "-cvjf", tarball, bundle]
        logging.info(cmd)

        subprocess.check_call(cmd)

        # make a sha1 of both the tarball and meta file

        tarball_hash = self.hash_file(tarball)

        fh = open(tarball_sha1, "w")
        fh.write(tarball_hash)
        fh.close()

        csv_hash = self.hash_file(csv_local)

        fh = open(csv_sha1, "w")
        fh.write(csv_hash)
        fh.close()

        # create a README and some basic info

        dt = datetime.datetime.now()

        fh = open(readme, 'w')
        fh.write("# %s\n\n" % bundle)
        fh.write("This bundle was generated by robots on %s\n" % dt.isoformat())
        fh.close()

        # now copy stuff to S3

        if self.bucket:
            self.store_remote(tarball)
            self.store_remote(tarball_sha1)
            self.store_remote(csv_local)
            self.store_remote(csv_sha1)
            self.store_remote(readme)
        else:
            logging.info("No AWS config so nothing is being copied to the SKY")

        # clean up

        self.cleanup(dirs, ())

    def hash_file(self, f):

        cmd = [ "sha1sum", f ]
        logging.info(cmd)
        
        out = subprocess.check_output(cmd)
        out = out.split(" ")
        
        hash = out[0]
        hash = hash.strip()
        
        return hash
    
    def cleanup(self, dirs, files):

        for d in dirs:
        
            if os.path.exists(d):
                logging.info("remove directory %s" % d)
                shutil.rmtree(d)                

        for f in files:

            if os.path.exists(f):
                logging.info("remove file %s" % f)
                os.unlink(f)

    def read_remote(self, abs_path):

        fname = os.path.basename(abs_path)
        rel_path = os.path.join("bundles", fname)

        k = Key(self.bucket)
        k.key = rel_path

        try:
            return k.get_contents_as_string()
        except Exception, e:
            return None

    def store_remote(self, abs_path):

        fname = os.path.basename(abs_path)
        rel_path = os.path.join("bundles", fname)

        k = Key(self.bucket)
        k.key = rel_path
        
        k.set_contents_from_filename(abs_path)
        k.set_acl('public-read')
