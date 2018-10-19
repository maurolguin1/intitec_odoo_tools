# Dropbox Backup Manteiner MFH

Odoo Database Backup Uploader to Dropbox User Account

1- Creamos la carpeta
---------------------------

```
mkdir /opt/odoo/backups
chown odoo: /opt/odoo/backups/ -R

```


2- Instalamos las Dependencias
-----------------------------
```
pip install requests
pip install urllib3
apt-get install build-essential libssl-dev libffi-dev python-dev
pip install pysftp
pip install cryptography
```

3- Instalamos la libreria de Dropbox
-----------
```
pip install dropbox==7.3.1
```

3a- Si tienes una version de la api superior a la 7 te dara problema desintala tu version actual con
-----------
```
pip uninstall dropbox
```


(See <a href="https://www.dropbox.com/developers-v1/core/sdks/python">Dropbox python documentation</a>)


4- Modification on urllib3 for bug fixing to correct file upload to Dropbox
---------------------------------------------------------------------------

Go to file  /usr/lib/python2.7/dist-packages/urllib3/contrib/pyopenssl.py

Substitue function sendall(self, data) on class WrappedSocket for this code:

    def send_until_done(self, data):
        while True:
            try:
                return self.connection.send(data)
            except OpenSSL.SSL.WantWriteError:
                _, wlist, _ = select.select([], [self.socket], [],
                                            self.socket.gettimeout())
                if not wlist:
                    raise
                continue

    def sendall(self, data):
        while len(data):
            sent = self.send_until_done(data)
            data = data[sent:]

For more information check this fix in this <a href="https://github.com/shazow/urllib3/issues/412">issue</a>.

5- Dropbox API Connection
-------------------------

The module communicates to the Dropbox API using the Access Token obtained following the steps of this <a href="https://www.dropbox.com/developers/apps/create">tutorial</a>


# Install

Go to https://www.dropbox.com/developers/apps and create a app, after you need a Token

![Alt text](https://github.com/falconsoft3d/odoo_general/blob/master/update_dropbox/static/description/dr0.png?raw=true "Optional Title")

1...
![Alt text](https://github.com/falconsoft3d/odoo_general/blob/master/update_dropbox/static/description/dr1.png?raw=true "Optional Title")

2...
![Alt text](https://github.com/falconsoft3d/odoo_general/blob/master/update_dropbox/static/description/dr2.png?raw=true "Optional Title")

3...
![Alt text](https://github.com/falconsoft3d/odoo_general/blob/master/update_dropbox/static/description/dr3.png?raw=true "Optional Title")

