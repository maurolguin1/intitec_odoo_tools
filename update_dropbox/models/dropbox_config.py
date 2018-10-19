# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _

class dropbox_config_settings(models.TransientModel):
    _name = 'dropbox.config.settings'
    _inherit = 'res.config.settings'

    token = fields.Char('Token', help="Application Access Token")

    @api.multi
    def set_token_defaults(self):
        return self.env['ir.values'].sudo().set_default('dropbox.config.settings', 'token', self.token)

    @api.multi
    def go_to_link(self):
        return {
            'type': 'ir.actions.act_url',
            'url': 'https://www.dropbox.com/developers/apps/create',
            'target': 'new',
        }
