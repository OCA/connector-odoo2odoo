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
        "product",
        "connector_base_product",
        "odoo2odoo_ir",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/product_uom_categ.xml",
        "views/product_uom.xml",
        "views/product_category.xml",
        "views/product_template.xml",
        "views/product_product.xml",
    ],
}
