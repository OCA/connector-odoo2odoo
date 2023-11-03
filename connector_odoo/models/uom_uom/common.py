# Copyright 2013-2017 Camptocamp SA
# © 2016 Sodexis
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import fields, models

from odoo.addons.component.core import Component


class OdooProductUOM(models.Model):
    _name = "odoo.uom.uom"
    _inherit = [
        "odoo.binding",
    ]
    _inherits = {"uom.uom": "odoo_id"}
    _description = "Odoo Product UOM"

    _sql_constraints = [
        (
            "external_id",
            "UNIQUE(external_id)",
            "External ID (external_id) must be unique!",
        ),
    ]

    """
    Product UOM are not fully managed with dependencies etc.
    User has the responsability to check the names are the same in
    both instances
    """

    def resync(self):
        if self.backend_id.main_record == "odoo":
            return self.with_delay().export_record(self.backend_id)
        else:
            return self.with_delay().import_record(
                self.backend_id, self.external_id, force=True
            )


class ProductUoM(models.Model):
    _inherit = "uom.uom"

    bind_ids = fields.One2many(
        comodel_name="odoo.uom.uom",
        inverse_name="odoo_id",
        string="Odoo Bindings",
    )


class ProductUoMAdapter(Component):
    _name = "odoo.uom.uom.adapter"
    _inherit = "odoo.adapter"
    _apply_on = "odoo.uom.uom"
    _odoo_model = "product.uom"
