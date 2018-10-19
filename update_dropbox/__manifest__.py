# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    This module copyright (C) 2017 Marlon Falcón Hernandez
#    (<http://www.falconsolutions.cl>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
    'name': 'Dropbox Backup Manteiner MFH',
    'version': '11.0.0.1.0',
    'author': 'Falcon Solutions SpA',
    'maintainer': 'Falcon Solutions',
    'website': 'http://www.falconsolutions.cl',
    'license': 'AGPL-3',
    'category': 'Settings',
    'summary': 'Dropbox Backup Manteiner',
    'depends': [
        'auto_backup'
    ],
    'description': """
Dropbox Backup Manteiner MFH
=====================================================
* Dropbox API interaction
* Creates daily db backup and uploads it into Dropbox User Account
* Go to Settings > Chilean Localization Settings > Dropbox Config
* Set the Access Token to Dropbox API
* Go to Settings > Technical > Back-ups > Configure Backups
* Check the Dropbox setting and set the recurrency of backup upload
        """,
    'data': [
        'security/ir.model.access.csv',
        'views/dropbox_config_view.xml',
        'views/dropbox_config.xml',
        'views/db_backup_view.xml',
    ],
    'external_dependencies': {
        'python': ['requests', 'dropbox', 'pysftp', 'urllib3'],
    },
    'installable': True,
    'auto_install': False,
    'demo': [],
    'test': [],
}
