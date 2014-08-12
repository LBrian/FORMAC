import os
import sys
import time
import logging
import easywebdav
from urllib import unquote_plus

def download_folder(logger, webdav, src, dest):
    webdav.cd(src)
    root_list = webdav.ls(src)
    if len(root_list) > 1:
        for fname in root_list:
            if fname.name == src:
                continue
	    decoded_fname = unquote_plus(fname.name)
            if os.path.exists(dest + decoded_fname):
                # local has a copy, sync up differences
                if fname.contenttype == "httpd/unix-directory":
                    # iterate folder
                    #logger.info("Synchronizing folder %s from Safesync", decoded_fname)
                    download_folder(logger, webdav, fname.name, dest)
                else:
                    local_mtime = os.path.getmtime(dest + decoded_fname)
                    mtime_s = str(fname.mtime).split(" ")
                    mtime_o = time.strptime(mtime_s[1]+" "+mtime_s[2]+" "+mtime_s[3]+" "+mtime_s[4], "%d %b %Y %H:%M:%S")
                    mtime_ts = time.mktime(mtime_o)
                    # if remote file has been changed then download the latest version
                    if mtime_ts > local_mtime:
                        os.remove(dest + decoded_fname)
                        logger.info("Synchronizing updated file %s from Safesync", decoded_fname)
                        webdav.download(fname.name, dest + decoded_fname)
            else:
                # is folder, recursive call
                if fname.contenttype == "httpd/unix-directory":
                    # iterate folder
                    logger.info("Downloading new folder %s from Safesync", decoded_fname)
                    os.mkdir(dest + decoded_fname)
                    download_folder(logger, webdav, fname.name, dest)
                else:
                    logger.info("Downloading new file %s from Safesync", decoded_fname)
                    webdav.download(fname.name, dest + decoded_fname)
    webdav.cd("/")
    return

if __name__ == '__main__':
    ## logging
    logging.basicConfig(filename='/var/log/safesync_agent.log', level=logging.WARNING)
    logger = logging.getLogger("[Safesync Agent]")

    ## create pid file
    pid = str(os.getpid())
    pidfile = "/tmp/safesync_agent.pid"
    if os.path.isfile(pidfile):
        logger.warning("%s already exists, exiting" % pidfile)
        sys.exit()
    else:
        f = open(pidfile, 'w')
        f.write(pid)
        f.close()

    ## Trend Micro Safesync configuration
    # APAC/America WebDAV server
    #safesync_host = "dav.dc1.safesync.com"
    # EMEA WebDAV server
    safesync_host = "dav.dc2.safesync.com"
    safesync_user = "safesynctest1@yopmail.com"
    safesync_pass = "safesynctest1"

    ## My Cloud path
    local_root = "/nfs/Public"
    ## Trend Micro Safesync path
    remote_root ="/"

    webdav = easywebdav.connect(host=safesync_host, username=safesync_user,
                                password=safesync_pass, protocol="https", port=443)
    ## root folder
    download_folder(logger, webdav, remote_root, local_root)

    ## remove pid file
    os.unlink(pidfile)
