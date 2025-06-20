# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class SkyDocumentFolder(models.Model):
    _name = 'sky.document.folder'
    _description = 'Document Folder'
    _parent_name = "parent_id"
    _parent_store = True
    _rec_name = 'complete_name'
    _order = 'parent_path'

    name = fields.Char(string='Name', required=True)
    complete_name = fields.Char(string='Complete Name', compute='_compute_complete_name', store=True)
    parent_id = fields.Many2one('sky.document.folder', string='Parent Folder', index=True, ondelete='cascade')
    parent_path = fields.Char(index=True)
    child_ids = fields.One2many('sky.document.folder', 'parent_id', string='Child Folders')
    document_ids = fields.One2many('sky.document', 'folder_id', string='Documents')
    document_count = fields.Integer(string='Document Count', compute='_compute_document_count')
    partner_id = fields.Many2one('res.partner', string='Contact', index=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, required=True, ondelete='restrict')
    active = fields.Boolean(default=True)
    user_id = fields.Many2one('res.users', string='Responsible', default=lambda self: self.env.user)
    color = fields.Integer(string='Color Index')

    @api.depends('name', 'parent_id.complete_name')
    def _compute_complete_name(self):
        for folder in self:
            if folder.parent_id:
                folder.complete_name = '%s / %s' % (folder.parent_id.complete_name, folder.name)
            else:
                folder.complete_name = folder.name

    @api.depends('document_ids', 'child_ids.document_count')
    def _compute_document_count(self):
        for folder in self:
            folder.document_count = len(folder.document_ids) + sum(child.document_count for child in folder.child_ids)

    @api.constrains('parent_id')
    def _check_parent_id(self):
        if not self._check_recursion():
            raise ValidationError(_('Error! You cannot create recursive folders.'))

    def action_view_documents(self):
        self.ensure_one()
        return {
            'name': _('Documents'),
            'domain': [('folder_id', '=', self.id)],
            'res_model': 'sky.document',
            'type': 'ir.actions.act_window',
            'view_mode': 'list,form',
            'context': {
                'default_folder_id': self.id,
                'form_view_ref': 'sky_documents.view_sky_document_form_simple',
            },
        }

    def get_document_count(self):
        self.ensure_one()
        return self.document_count
