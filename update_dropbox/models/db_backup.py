# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import xmlrpc.client
import socket
import requests
import os, sys
import shutil
import functools
import time
import datetime
import base64
import re
import logging
import dropbox

from odoo import models, fields, api, tools, _
from odoo.exceptions import Warning

try:
    import pysftp
except ImportError:
    raise ImportError(_('This module needs pysftp to automaticly write backups to the FTP through SFTP. Please install pysftp on your system. (sudo pip install pysftp)'))

_logger = logging.getLogger(__name__)

def execute(connector, method, *args):
    res = False
    try:
        res = getattr(connector,method)(*args)
    except socket.error as e:
            raise e
    return res

class UpdateDropboxDbBackup(models.Model):
    _inherit = 'db.backup'
    
    folder = fields.Char('Backup Directory', help='Absolute path for storing the backups', required='True',
                         default='/tmp/odoo')
    dropbox_upload = fields.Boolean('Upload backup in Dropbox', help="If you check this option you can specify the details needed to upload backups into a Dropbox User Account.")
    recurrency = fields.Selection([('daily', 'Daily'),('weekly', 'Weekly'), ('monthly', 'Monthly')], 'Recurrency', default='weekly',help="Defines the recurrency of backups to be upload in Dropbox")
    send_mail = fields.Boolean('Send Confirmation Mail',help="Send upload confirmation mail")
    send_to = fields.Char('Confirmation EMail',help="Recipient email to the upload confirmation mail")

    @api.multi
    def schedule_backup(self):
        """Overwrite function for dropbox uploading addition"""
        conf_ids = self.search([])
        for rec in conf_ids:
            db_list = self.get_db_list(rec.host, rec.port)

            if rec.name in db_list:
                try:
                    if not os.path.isdir(rec.folder):
                        os.mkdir( rec.folder, 0o755 )
                        #os.makedirs(rec.folder, 777)
                except:
                    raise
                #Create name for dumpfile.
                bkp_file='%s_%s.%s' % (time.strftime('%d_%m_%Y_%H_%M_%S'),rec.name, rec.backup_type)
                file_path = os.path.join(rec.folder,bkp_file)
                uri = 'http://' + rec.host + ':' + rec.port
                
                conn = xmlrpc.client.ServerProxy(uri + '/xmlrpc/db')
                bkp=''
                try:
                    bkp_resp = requests.post(
                        uri + '/web/database/backup', stream = True,
                        data = {
                            'master_pwd': tools.config['admin_passwd'],
                            'name': rec.name,
                            'backup_format': rec.backup_type
                        }
                    )
                    bkp_resp.raise_for_status()
                except:
                    _logger.error(_("Couldn't backup database %s. Bad database administrator password for server running at http://%s:%s" %(rec.name, rec.host, rec.port)))
                    continue
                #with os.#open(file_path,'w+') as fp:
                with open(file_path,'wb') as fp:
                    # see https://github.com/kennethreitz/requests/issues/2155
                    bkp_resp.raw.read = functools.partial(
                        bkp_resp.raw.read, decode_content=True)
                    shutil.copyfileobj(bkp_resp.raw, fp)
            else:
                _logger.error(_("database %s doesn't exist on http://%s:%s" %(rec.name, rec.host, rec.port)))

            #Check if user wants to upload backup in a Dropbox Account
            if rec.dropbox_upload:
                try:
                    token = self.env['ir.values'].get_defaults_dict('dropbox.config.settings').get('token')
                    # client = dropbox.client.DropboxClient(token)
                    client = dropbox.Dropbox(token)

                    if os.path.isfile(file_path):
                        extension = os.path.splitext(file_path)[1]
                        os.chmod(file_path, 0o775)
                        fi = open(str(file_path), 'rb')
                        filename = ''
                        create_date = datetime.datetime.now()
                        """
                        if rec.recurrency == 'daily':
                            filename = create_date.day
                        if rec.recurrency == 'weekly':
                            filename = create_date.isoweekday()
                        if rec.recurrency == 'monthly':
                            filename = create_date.month
                        """
                        # fname = '%s_%s'%(rec.name,str(filename).zfill(2))
                        # fname = str(create_date)[0:19].replace(":", '_').replace(" ", '_').replace("-",'_') + ".zip"
                        fname = '%s_%s' % (rec.name, str(create_date)[0:19].replace(":", '_').replace(" ", '_').replace("-",'_') + ".zip")
                        try:
                            # response = client.put_file('/%s%s'%(fname,extension),fi,overwrite=True)
                            response = client.files_upload(fi.read(), '/' + fname + extension)
                            _logger.info(_('Succesfully file upload: %s%s' %(fname,extension)))
                            if rec.send_mail:
                                try:
                                    user = self.env['res.users'].browse(self.env.uid)
                                    ir_mail_server = self.env['ir.mail_server']
                                    message = _("Dear,\n\nThe backup for the server " + rec.host + " it's been uploaded successfully to your Dropbox account.")
                                    msg = ir_mail_server.build_email(user.email, [rec.send_to], "Backup from " + rec.host + " uploaded successfully!", message)
                                    ir_mail_server.send_email(msg)
                                except Exception:
                                    _logger.error(_('Exception! The message couldn\'t be sent'))
                                    pass
                        except:
                            _logger.error(_('Exception! We couldn\'t upload the file %s to the Dropbox user account'%file_path))
                            continue
                except Exception as e:
                    _logger.error(_('Exception! Something is wrong with the Dropbox API connection'))
                
            # Check if user wants to write to SFTP or not.
            if rec.sftp_write is True:
                try:
                    # Store all values in variables
                    dir = rec.folder
                    pathToWriteTo = rec.sftp_path
                    ipHost = rec.sftp_host
                    portHost = rec.sftp_port
                    usernameLogin = rec.sftp_user
                    passwordLogin = rec.sftp_password
                    # Connect with external server over SFTP
                    srv = pysftp.Connection(host=ipHost, username=usernameLogin, password=passwordLogin, port=portHost)
                    # set keepalive to prevent socket closed / connection dropped error
                    srv._transport.set_keepalive(30)
                    # Move to the correct directory on external server. If the user made a typo in his path with multiple slashes (/odoo//backups/) it will be fixed by this regex.
                    pathToWriteTo = re.sub('([/]{2,5})+','/',pathToWriteTo)
                    _logger.debug(_('sftp remote path: %s' % pathToWriteTo))
                    try:
                        srv.chdir(pathToWriteTo)
                    except IOError:
                        #Create directory and subdirs if they do not exist.
                        currentDir = ''
                        for dirElement in pathToWriteTo.split('/'):
                            currentDir += dirElement + '/'
                            try:
                                srv.chdir(currentDir)
                            except:
                                _logger.info(_('(Part of the) path didn\'t exist. Creating it now at ' + currentDir))
                                #Make directory and then navigate into it
                                srv.mkdir(currentDir, mode=777)
                                srv.chdir(currentDir)
                                pass
                    srv.chdir(pathToWriteTo)
                    # Loop over all files in the directory.
                    for f in os.listdir(dir):
                        if rec.name in f:
                            fullpath = os.path.join(dir, f)
                            if os.path.isfile(fullpath):
                                if not srv.exists(f):
                                    _logger.info(_('The file %s is not yet on the remote FTP Server ------ Copying file' % fullpath))
                                    srv.put(fullpath)
                                    _logger.info('Copying File % s------ success' % fullpath)
                                else:
                                    _logger.error(_('File %s already exists on the remote FTP Server ------ skipped' % fullpath))

                    # Navigate in to the correct folder.
                    srv.chdir(pathToWriteTo)

                    # Loop over all files in the directory from the back-ups.
                    # We will check the creation date of every back-up.
                    for file in srv.listdir(pathToWriteTo):
                        if rec.name in file:
                            # Get the full path
                            fullpath = os.path.join(pathToWriteTo,file)
                            # Get the timestamp from the file on the external server
                            timestamp = srv.stat(fullpath).st_atime
                            createtime = datetime.datetime.fromtimestamp(timestamp)
                            now = datetime.datetime.now()
                            delta = now - createtime
                            # If the file is older than the days_to_keep_sftp (the days to keep that the user filled in on the Odoo form it will be removed.
                            if delta.days >= rec.days_to_keep_sftp:
                                # Only delete files, no directories!
                                if srv.isfile(fullpath) and (".dump" in file or '.zip' in file):
                                    _logger.info(_("Delete too old file from SFTP servers: " + file))
                                    srv.unlink(file)
                    # Close the SFTP session.
                    srv.close()
                except Exception as e:
                    _logger.error(_('Exception! We couldn\'t back up to the FTP server..'))
                    #At this point the SFTP backup failed. We will now check if the user wants
                    #an e-mail notification about this.
                    if rec.send_mail_sftp_fail:
                        try:
                            ir_mail_server = self.pool.get('ir.mail_server')
                            message = _("Dear,\n\nThe backup for the server " + rec.host + " (IP: " + rec.sftp_host + ") failed.Please check the following details:\n\nIP address SFTP server: " + rec.sftp_host + "\nUsername: " + rec.sftp_user + "\nPassword: " + rec.sftp_password + "\n\nError details: " + tools.ustr(e) + "\n\nWith kind regards")
                            msg = ir_mail_server.build_email("auto_backup@" + rec.name + ".com", [rec.email_to_notify], "Backup from " + rec.host + "(" + rec.sftp_host + ") failed", message)
                            ir_mail_server.send_email(cr, user, msg)
                        except Exception:
                            pass

            """
            Remove all old files (on local server) in case this is configured..
            """
            if rec.autoremove:
                dir = rec.folder
                # Loop over all files in the directory.
                for f in os.listdir(dir):
                    fullpath = os.path.join(dir, f)
                    # Only delete the ones wich are from the current database (Makes it possible to save different databases in the same folder)
                    if rec.name in fullpath:
                        timestamp = os.stat(fullpath).st_ctime
                        createtime = datetime.datetime.fromtimestamp(timestamp)
                        now = datetime.datetime.now()
                        delta = now - createtime
                        if delta.days >= rec.days_to_keep:
                            # Only delete files (which are .dump and .zip), no directories.
                            if os.path.isfile(fullpath) and (".dump" in f or '.zip' in f):
                                _logger.info(_("Delete local out-of-date file: " + fullpath))
                                os.remove(fullpath)
