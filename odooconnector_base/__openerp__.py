# -*- coding: utf-8 -*-
# © 2015 Malte Jacobi (maljac @ github)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    'name': 'Odoo Connector - Base',
    'summary': 'Base connector for Odoo2Odoo scenarios',
    'version': '8.0.1.0.0',
    'category': 'Connector',
    'website': 'https://odoo-community.org/',
    'author': 'IBO Institut (Malte Jacobi), Odoo Community Association (OCA)',
    'license': 'AGPL-3',
    'application': True,
    'installable': True,
    'external_dependencies': {
        'python': ['oerplib'],
    },
    'depends': [
        'base',
        'product',
        'connector',
    ],
    'data': [
        'security/odooconnector_base_security.xml',
        'data/odooconnector_base.xml',
        'views/odooconnector_backend.xml',
        'views/partner.xml',
        'views/product.xml',
        'views/product_uom.xml',
    ],
    'demo': [
    ],
}
