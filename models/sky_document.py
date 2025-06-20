# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import base64
import mimetypes


class SkyDocumentTab(models.Model):
    _name = 'sky.document.tab'
    _description = 'Document Tab'
    _order = 'sequence, name'

    name = fields.Char(string='Name', required=True)
    sequence = fields.Integer(string='Sequence', default=10)
    color = fields.Integer(string='Color Index')
    active = fields.Boolean(default=True)
    is_default = fields.Boolean(string='Default Tab', default=False)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, required=True, ondelete='restrict')
    document_ids = fields.One2many('sky.document', 'tab_id', string='Documents')
    document_count = fields.Integer(string='Document Count', compute='_compute_document_count')

    @api.depends('document_ids')
    def _compute_document_count(self):
        for tab in self:
            tab.document_count = len(tab.document_ids)

    @api.model
    def create(self, vals):
        # If this is set as the default tab, unset any other default tabs
        if vals.get('is_default'):
            self.search([('is_default', '=', True)]).write({'is_default': False})
        return super(SkyDocumentTab, self).create(vals)

    def write(self, vals):
        # If this is set as the default tab, unset any other default tabs
        if vals.get('is_default'):
            self.search([('id', 'not in', self.ids), ('is_default', '=', True)]).write({'is_default': False})
        return super(SkyDocumentTab, self).write(vals)

    @api.model
    def _get_default_tab(self):
        # Get the default tab, or create one if none exists
        default_tab = self.search([('is_default', '=', True)], limit=1)
        if not default_tab:
            default_tab = self.search([], limit=1, order='sequence, id')
        if not default_tab:
            default_tab = self.create({
                'name': 'Client',
                'is_default': True,
                'sequence': 1,
            })
        return default_tab

    def action_view_documents(self):
        self.ensure_one()
        return {
            'name': _('Documents'),
            'domain': [('tab_id', '=', self.id)],
            'res_model': 'sky.document',
            'type': 'ir.actions.act_window',
            'view_mode': 'list,form',
            'context': {
                'default_tab_id': self.id,
                'form_view_ref': 'sky_documents.view_sky_document_form_simple',
            },
        }


class SkyDocument(models.Model):
    _name = 'sky.document'
    _description = 'SKY Document'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'tab_id, create_date desc'

    name = fields.Char(string='Name', required=True, tracking=True)
    file = fields.Binary(string='File', attachment=True, required=True)
    file_name = fields.Char(string='File Name')
    file_size = fields.Integer(string='Taille', compute='_compute_file_size', store=True)
    file_type = fields.Char(string='Type', compute='_compute_file_type', store=True)
    comment = fields.Text(string='Comment')
    tag_ids = fields.Many2many('sky.document.tag', string='Tags')
    folder_id = fields.Many2one('sky.document.folder', string='Folder')
    tab_id = fields.Many2one('sky.document.tab', string='Tab', index=True, 
                             default=lambda self: self.env['sky.document.tab']._get_default_tab())
    partner_id = fields.Many2one('res.partner', string='Client', index=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, required=True, ondelete='restrict')
    is_image = fields.Boolean(string='Is Image', compute='_compute_file_type', store=True)
    is_pdf = fields.Boolean(string='Is PDF', compute='_compute_file_type', store=True)
    thumbnail = fields.Binary(string='Thumbnail', attachment=True, compute='_compute_thumbnail', store=True)
    active = fields.Boolean(default=True)

    @api.depends('file')
    def _compute_file_size(self):
        for record in self:
            if record.file:
                # Convert bytes to KB
                record.file_size = len(base64.b64decode(record.file)) // 1024
            else:
                record.file_size = 0

    @api.depends('file_name', 'file')
    def _compute_file_type(self):
        for record in self:
            if record.file_name:
                # Extract only the file extension
                extension = record.file_name.split('.')[-1] if '.' in record.file_name else ''
                mime_type, _ = mimetypes.guess_type(record.file_name)
                record.file_type = extension.lower() if extension else ''
                record.is_image = mime_type and mime_type.startswith('image/') or False
                record.is_pdf = mime_type == 'application/pdf' or False
            else:
                record.file_type = ''
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
    def default_get(self, fields_list):
        res = super(SkyDocument, self).default_get(fields_list)
        # If we're in a contact form and no partner_id is set yet, use the active_id as partner_id
        if not res.get('partner_id') and self._context.get('active_model') == 'res.partner' and self._context.get('active_id'):
            res['partner_id'] = self._context.get('active_id')
        return res

    @api.model
    def create(self, vals):
        if 'file' in vals and 'file_name' in vals and not vals.get('name'):
            vals['name'] = vals['file_name']

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
