# -*- coding: utf-8 -*-
# Copyright 2016 ABF OSIELL <http://osiell.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Odoo2Odoo - Backend",
    "summary": "Framework to sync data between Odoo servers.",
    "version": "8.0.1.0.0",
    "category": "Tools",
    "website": "http://osiell.com/",
    "author": "ABF OSIELL, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "external_dependencies": {
        "python": ['odoorpc'],
    },
    "depends": [
        "connector",
        "odoo2odoo_node",
    ],
    "data": [
        "security/ir.model.access.csv",
        'data/odoo_backend.xml',
        'views/menu.xml',
        'views/backend.xml',
    ],
}
