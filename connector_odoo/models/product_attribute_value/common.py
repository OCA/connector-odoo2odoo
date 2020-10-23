# -*- coding: utf-8 -*-
# Copyright 2013-2017 Camptocamp SA
# © 2016 Sodexis
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import fields, models
from odoo.addons.component.core import Component


class OdooProductAttributeValue(models.Model):
    _name = "odoo.product.attribute.value"
    _inherit = ["odoo.binding"]
    _inherits = {"product.attribute.value": "odoo_id"}
    _description = "Odoo Product Attribute Value"

    bind_ids = fields.One2many(
        comodel_name="odoo.product.attribute.value",
        inverse_name="odoo_id",
        string="Odoo Bindings",
    )


class OdooProductAttributeAdapter(Component):
    _name = "odoo.product.attribute.value.adapter"
    _inherit = "odoo.adapter"
    _apply_on = "odoo.product.attribute.value"
    _odoo_model = "product.attribute.value"
