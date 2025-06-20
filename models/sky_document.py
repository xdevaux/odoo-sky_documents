# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import base64
import mimetypes

class SkyDocument(models.Model):
    _name = 'sky.document'
    _description = 'SKY Document'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    name = fields.Char(string='Name', required=True, tracking=True)
    file = fields.Binary(string='File', attachment=True, required=True)
    file_name = fields.Char(string='File Name')
    file_size = fields.Integer(string='File Size', compute='_compute_file_size', store=True)
    file_type = fields.Char(string='File Type', compute='_compute_file_type', store=True)
    comment = fields.Text(string='Comment')
    tag_ids = fields.Many2many('sky.document.tag', string='Tags')
    folder_id = fields.Many2one('sky.document.folder', string='Folder')
    partner_id = fields.Many2one('res.partner', string='Contact', index=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, required=True, ondelete='restrict')
    is_image = fields.Boolean(string='Is Image', compute='_compute_file_type', store=True)
    is_pdf = fields.Boolean(string='Is PDF', compute='_compute_file_type', store=True)
    thumbnail = fields.Binary(string='Thumbnail', attachment=True, compute='_compute_thumbnail', store=True)
    active = fields.Boolean(default=True)

    @api.depends('file')
    def _compute_file_size(self):
        for record in self:
            if record.file:
                record.file_size = len(base64.b64decode(record.file))
            else:
                record.file_size = 0

    @api.depends('file_name', 'file')
    def _compute_file_type(self):
        for record in self:
            if record.file_name:
                mime_type, _ = mimetypes.guess_type(record.file_name)
                record.file_type = mime_type or 'application/octet-stream'
                record.is_image = mime_type and mime_type.startswith('image/') or False
                record.is_pdf = mime_type == 'application/pdf' or False
            else:
                record.file_type = 'application/octet-stream'
                record.is_image = False
                record.is_pdf = False

    @api.depends('file', 'is_image')
    def _compute_thumbnail(self):
        for record in self:
            if record.is_image:
                record.thumbnail = record.file
            else:
                record.thumbnail = False

    @api.model
    def create(self, vals):
        if 'file' in vals and 'file_name' in vals and not vals.get('name'):
            vals['name'] = vals['file_name']

        # If partner_id is provided but no folder_id, find or create a "Client" folder
        if vals.get('partner_id') and not vals.get('folder_id'):
            partner_id = vals['partner_id']

            # Search for a "Client" folder for this partner
            client_folder = self.env['sky.document.folder'].search([
                ('name', '=', 'Client'),
                ('partner_id', '=', partner_id),
                ('parent_id', '=', False)  # Root folder
            ], limit=1)

            # If no "Client" folder exists, create one
            if not client_folder:
                client_folder = self.env['sky.document.folder'].create({
                    'name': 'Client',
                    'partner_id': partner_id,
                })

            # Set the folder_id to the "Client" folder
            vals['folder_id'] = client_folder.id

        return super(SkyDocument, self).create(vals)

    def action_open_document(self):
        self.ensure_one()

        # For PDF and images, use Odoo's built-in document viewer
        if self.is_pdf or self.is_image:
            attachment_id = self.env['ir.attachment'].search([
                ('res_model', '=', self._name),
                ('res_id', '=', self.id),
                ('res_field', '=', 'file')
            ], limit=1)

            if attachment_id:
                return {
                    'type': 'ir.actions.act_url',
                    'url': '/web/content/%s?download=false&filename=%s&t=%s' % (
                        attachment_id.id, self.file_name, fields.Datetime.now()),
                    'target': 'new',
                }

        # For other file types or if attachment not found, download the file
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/%s/%s/file/%s?download=true&t=%s' % (
                self._name, self.id, self.file_name, fields.Datetime.now()),
            'target': 'self',
        }


class SkyDocumentTag(models.Model):
    _name = 'sky.document.tag'
    _description = 'Document Tag'

    name = fields.Char(string='Name', required=True)
    color = fields.Integer(string='Color Index')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, required=True, ondelete='restrict')
