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

        # Check if a "Client" folder exists for this partner
        client_folder = self.env['sky.document.folder'].search([
            ('name', '=', 'Client'),
            ('partner_id', '=', self.id),
            ('parent_id', '=', False)  # Root folder
        ], limit=1)

        # If no "Client" folder exists, create one
        if not client_folder:
            client_folder = self.env['sky.document.folder'].create({
                'name': 'Client',
                'partner_id': self.id,
            })

        # Return action to view folders
        return {
            'name': _('Documents'),
            'domain': [('partner_id', '=', self.id)],
            'res_model': 'sky.document.folder',
            'type': 'ir.actions.act_window',
            'view_mode': 'list,form',
            'context': {
                'default_partner_id': self.id,
                'search_default_root_folders': 1,
            },
        }

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
