# -*- coding: utf-8 -*-
# Copyright 2017 Florent THOMAS (Mind And Go), Odoo Community Association (OCA)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Connector Odoo",
    "summary": """
        Base connector for Odoo To Odoo scenarios""",
    "version": "10.0.1.0.0",
    "category": "Connector",
    "license": "AGPL-3",
    "author": "Florent THOMAS (Mind And Go), Odoo Community Association (OCA)",
    "application": False,
    "installable": True,
    "external_dependencies": {"python": ["odoorpc"], "bin": []},
    "depends": ["base", "product", "connector", "connector_base_product"],
    "data": [
        "security/connector_odoo_base_security.xml",
        "security/ir.model.access.csv",
        "views/odoo_backend.xml",
        "views/product_uom.xml",
        "views/odoo_connector_menus.xml",
        "views/product.xml",
        "views/product_template.xml",
        "wizards/add_backend.xml",
    ],
    "demo": [],
    "qweb": [],
}
