# Copyright 2013-2017 Camptocamp SA
# © 2016 Sodexis
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import fields, models

from odoo.addons.component.core import Component

_logger = logging.getLogger(__name__)


class OdooPartnerCategory(models.Model):
    _name = "odoo.res.partner.category"
    _inherit = "odoo.binding"
    _inherits = {"res.partner.category": "odoo_id"}
    _description = "External Odoo Partner Category"

    _sql_constraints = [
        (
            "external_id",
            "UNIQUE(external_id)",
            "External ID (external_id) must be unique!",
        ),
    ]

    def resync(self):
        if self.backend_id.main_record == "odoo":
            return self.with_delay().export_record(self.backend_id)
        else:
            return self.with_delay().import_record(
                self.backend_id, self.external_id, force=True
            )


class PartnerCategory(models.Model):
    _inherit = "res.partner.category"

    bind_ids = fields.One2many(
        comodel_name="odoo.res.partner.category",
        inverse_name="odoo_id",
        string="Odoo Bindings",
    )


class PartnerCategoryAdapter(Component):
    _name = "odoo.res.partner.category.adapter"
    _inherit = "odoo.adapter"
    _apply_on = "odoo.res.partner.category"

    _odoo_model = "res.partner.category"


class PartnerCategoryListener(Component):
    _name = "res.partner.category.listener"
    _inherit = "base.connector.listener"
    _apply_on = ["res.partner.category"]
    _usage = "event.listener"
