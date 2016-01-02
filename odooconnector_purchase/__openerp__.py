# -*- coding: utf-8 -*-
# © 2015 Malte Jacobi (maljac @ github)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    'name': 'Odoo Connector - Purchase',
    'summary': 'Technical base for purchase related Odoo Connector scenarios',
    'version': '8.0.1.0.0',
    'category': 'Connector',
    'website': 'https://odoo-community.org/',
    'author': 'IBO Institut (Malte Jacobi), Odoo Community Association (OCA)',
    'license': 'AGPL-3',
    'application': True,
    'installable': True,
    'external_dependencies': {
    },
    'depends': [
        'base',
        'purchase',
        'odooconnector_base',
    ],
    'data': [
        'views/purchase.xml',
    ],
    'demo': [
    ],
}
