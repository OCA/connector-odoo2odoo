# -*- coding: utf-8 -*-
# Copyright 2018 ABF OSIELL <http://osiell.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Odoo2Odoo - Products",
    "summary": "Sync products between Odoo servers.",
    "version": "8.0.1.0.0",
    "category": "Tools",
    "website": "http://osiell.com/",
    "author": "ABF OSIELL, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "odoo2odoo_backend",
        "product",
    ],
    "data": [
        "security/ir.model.access.csv",
    ],
}
