# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class ResPartner(models.Model):
    _inherit = 'res.partner'

    sky_document_ids = fields.One2many('sky.document', 'partner_id', string='Documents')
    sky_document_count = fields.Integer(string='Document Count', compute='_compute_sky_document_count')
    sky_folder_ids = fields.One2many('sky.document.folder', 'partner_id', string='Document Folders')

    @api.depends('sky_document_ids')
    def _compute_sky_document_count(self):
        for partner in self:
            partner.sky_document_count = len(partner.sky_document_ids)

    def action_view_sky_documents(self):
        self.ensure_one()

        # Get or create the 'Client' tab
        client_tab = self.env['sky.document.tab'].search([('name', '=', 'Client'), ('is_default', '=', True)], limit=1)
        if not client_tab:
            client_tab = self.env['sky.document.tab']._get_default_tab()

        # Return action to view documents directly
        action = self.env.ref('sky_documents.action_sky_document_from_partner').read()[0]
        action['domain'] = [('partner_id', '=', self.id)]
        action['context'] = {
            'default_partner_id': self.id,
            'default_tab_id': client_tab.id,
            'form_view_ref': 'sky_documents.view_sky_document_form_simple',
            'group_by': 'tab_id',
        }
        return action

    def action_view_sky_folders(self):
        self.ensure_one()
        return {
            'name': _('Document Folders'),
            'domain': [('partner_id', '=', self.id)],
            'res_model': 'sky.document.folder',
            'type': 'ir.actions.act_window',
            'view_mode': 'list,form',
            'context': {'default_partner_id': self.id},
        }
