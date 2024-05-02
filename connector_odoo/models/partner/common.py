# Copyright 2013-2017 Camptocamp SA
# © 2016 Sodexis
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import ast
import logging

from odoo import fields, models

from odoo.addons.component.core import Component

_logger = logging.getLogger(__name__)


class OdooPartner(models.Model):
    _name = "odoo.res.partner"
    _inherit = "odoo.binding"
    _inherits = {"res.partner": "odoo_id"}
    _description = "External Odoo Partner"

    _sql_constraints = [
        (
            "external_id",
            "UNIQUE(external_id)",
            "External ID (external_id) must be unique!",
        ),
    ]

    def name_get(self):
        result = []
        for op in self:
            name = "{} (Backend: {})".format(
                op.odoo_id.display_name, op.backend_id.display_name
            )
            result.append((op.id, name))

        return result

    def resync(self):
        if self.backend_id.main_record == "odoo":
            return self.with_delay().export_record(self.backend_id)
        else:
            return self.with_delay().import_record(
                self.backend_id, self.external_id, force=True
            )


class Partner(models.Model):
    _inherit = "res.partner"

    bind_ids = fields.One2many(
        comodel_name="odoo.res.partner",
        inverse_name="odoo_id",
        string="Odoo Bindings",
    )


class PartnerAdapter(Component):
    _name = "odoo.res.partner.adapter"
    _inherit = "odoo.adapter"
    _apply_on = "odoo.res.partner"

    _odoo_model = "res.partner"

    def search(self, filters=None, model=None, offset=0, limit=None, order=None):
        """Search records according to some criteria
        and returns a list of ids

        :rtype: list
        """
        if filters is None:
            filters = []
        ext_filter = ast.literal_eval(
            str(self.backend_record.external_partner_domain_filter)
        )
        filters += ext_filter or []
        return super(PartnerAdapter, self).search(
            filters=filters, model=model, offset=offset, limit=limit, order=order
        )


class PartnerListener(Component):
    _name = "res.partner.listener"
    _inherit = "base.connector.listener"
    _apply_on = ["res.partner"]
    _usage = "event.listener"
