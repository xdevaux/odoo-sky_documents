{
    'name': 'SKY Documents',
    'version': '2.5',
    'category': 'Document Management',
    'summary': 'Document management system with folder structure',
    'description': """
SKY Documents
============
This module provides document management functionality with:
- Document attachment to contacts
- Smart button on contact form
- Folder and subfolder organization
- Document preview and download
- Drag and drop upload
- Document metadata (comments, labels)
    """,
    'author': 'SKY',
    'website': '',
    'depends': ['base', 'contacts', 'mail', 'web'],
    'data': [
        'security/ir.model.access.csv',
        'views/sky_document_views.xml',
        'views/sky_document_folder_views.xml',
        'views/res_partner_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'sky_documents/static/src/js/sky_documents.js',
            'sky_documents/static/src/scss/sky_documents.scss',
        ],
    },
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
