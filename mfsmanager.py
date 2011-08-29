#!/usr/bin/python
    
import sys,os
import thread

import lxml
import llfuse
import logging

import mfs


def export_files(manifest_path, destination_path, export_type, config):
    """creates all files form the manifest in the provided directory"""

    datastore = mfs.datastore.Datastore(config.datastore)
    manifest = mfs.manifest.serializer.fromXML(manifest_path)
    manifest.export(destination_path, datastore, export_type)

def import_files(path):
    """traveres through given path and creates a manifest"""
    manifest = mfs.manifest.serializer.fromPath(path)
    print lxml.etree.tostring(manifest.toXML(), pretty_print=True)

def datastore_cleanup(manifests):
    """removes all files that are not in the manifest files provied as an argument"""

    hashes = list()

    for manifest_path in manifests:
        manifest = mfs.manifest.serializer.fromXML(manifest_path)
        hashes += manifest.get_hashes()

    datastore = mfs.datastore.Datastore(config.datastore)

    todel = set(datastore.contents()) - set(hashes)
    for filehash in todel:
        print "removing " + datastore.toPath(filehash)
        datastore.remove(filehash)

def mount_manifest(manifest_path, mountpoint_path):
    #init logging
    formatter = logging.Formatter('%(message)s') 
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    handler.setLevel(logging.DEBUG)
    log = logging.getLogger()
    log.setLevel(logging.INFO)    
    log.addHandler(handler)

    manifest = mfs.manifest.serializer.fromXML(manifest_path)
    datastore = mfs.datastore.Datastore(config.datastore)
    operations = mfs.fs.Operations(
        manifest,
        datastore)

    llfuse.init(operations, mountpoint_path, [])
    llfuse.main(single=False)
    llfuse.close()

def diff(file_a, file_b):
    manifest_a = mfs.manifest.serializer.fromXML(file_a)
    manifest_b = mfs.manifest.serializer.fromXML(file_b)

    for line in manifest_a.diff(manifest_b):
        print line


def datastore_store(manifest_path):
    """stores all files specified in the manifest in the provided datastore location"""
    manifest = mfs.manifest.serializer.fromXML(config.datastore)
    datastore = mfs.datastore.Datastore(config.datastore)

    for node in manifest:
        if (isinstance (node, mfs.manifest.nodes.File)
            and not datastore.contains(node)):
            print "storing {0}".format(source + node.path)
            datastore.saveData(node, source + node.path)

def datastore_fsck(datastore_path):
    """checks the files in the datastore for consistency"""
    datastore = mfs.datastore.Datastore(datastore_path)

    for filehash in datastore.contents():
        if not datastore.check(filehash):
            print "error in " + filehash

if __name__ == "__main__":
    
    help_message = """usage: {0} <config> <command> [<args>]""".format(sys.argv[0])
    help_message += """\navailable commands are:"""
    help_message += """\n   import : create a manifest from a directory"""
    help_message += """\n   export : store contents of a manifest to a directory"""
    help_message += """\n   store  : store files to datastore"""
    help_message += """\n   clean  : remove unneded files form datastore"""
    help_message += """\n   fsck   : check the datastore for file corruption"""
    help_message += """\n   diff   : compare two manifest files"""
    help_message += """\n   mount  : mount manifest to mountpoint"""

    config    = None
    action    = None
    arguments = None

    try:
        with open(sys.argv[1]) as configfile:
            config = mfs.config.Config(configfile)
        action = sys.argv[2]
        arguments = sys.argv[3:]
    except IndexError:
        print help_message
        print sys.argv[0] + " too few arguments"
        sys.exit(1)


    if (action == "export"):
        try:
            manifest_path    = arguments[0]
            destination_path = arguments[1]
            export_type      = None
    
            if len(arguments) == 3:
                export_type = arguments[2]
                if not (export_type == 'aufs' or export_type == 'unionfs'):
                    raise IndexError
        except IndexError as e:
            print "usage: {0} export MANIFEST DESTINATION [aufs,unionfs]".format(sys.argv[0])
            sys.exit(1)

        if not (os.path.exists(destination_path) and os.path.isdir(destination_path)):
            print ("ERROR: %s not a directory" % dir)
            sys.exit(1)
        export_files(manifest_path, destination_path, export_type, config)

    if (action == "import"):
        try:
            import_files(arguments[0])
        except IndexError:
            print "usage: {0} import PATH".format(sys.argv[0])
            sys.exit(1)

    if (action == "store"):
        try:
            datastore_store(arguments[0], arguments[1])
        except IndexError:
            print "usage {0} store SOURCE XML".format(sys.argv[0])
            sys.exit(1)

    if (action == "fsck"):
        try:
            datastore_fsck(arguments[0])
        except IndexError:
            print "usage {0} fsck".format(sys.argv[0])
            sys.exit(1)

    if (action == "diff"):
        try:
            diff(arguments[0], arguments[1])
        except IndexError:
            print "usage {0} diff FILE_A FILE_B".format(sys.argv[0])
            sys.exit(1)

    if (action == "cleanup"):
        try:
            datastore_cleanup(arguments)
        except IndexError:
            print "usage {0} cleanup MANIFEST [MANIFEST [MANIFEST ...".format(sys.argv[0])
            
    if (action == "mount"):
        try:
            mount_manifest(
                manifest_path = arguments[0],
                mountpoint_path = arguments[1])
        except IndexError as e:
            print e
            print "usage {0} mount MANIFEST MOUNTPOINT".format(sys.argv[0])
