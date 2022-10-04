# Copyright 2022 Greenice, S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import logging

from odoo import fields, models

from odoo.addons.component.core import Component

_logger = logging.getLogger(__name__)


class OdooResCurrencyRate(models.Model):
    _name = "odoo.res.currency.rate"
    _inherit = [
        "odoo.binding",
    ]
    _inherits = {"res.currency.rate": "odoo_id"}
    _description = "Odoo Currency rate"

    _sql_constraints = [
        (
            "external_id",
            "UNIQUE(external_id)",
            "External ID (external_id) must be unique!",
        ),
    ]

    def resync(self):
        if self.backend_id.main_record == "odoo":
            raise NotImplementedError
        else:
            return self.with_delay().import_record(
                self.backend_id, self.external_id, force=True
            )

    def import_rate(self, backend_record, rate_id, currency_id):
        _logger.info("Obtaining Currency rate {}".format(rate_id))
        currency_rate_model = backend_record.get_connection().api.get(
            "res.currency.rate"
        )
        rate = currency_rate_model.browse(rate_id)
        currency_id = (
            self.env["odoo.res.currency"]
            .search([("external_id", "=", currency_id)])
            .odoo_id
        )
        payload = {"currency_id": currency_id.id, "name": rate.name, "rate": rate.rate}
        link_id = self.env["odoo.res.currency.rate"].search(
            [("external_id", "=", rate_id)]
        )
        if link_id:
            link_id.odoo_id.write(payload)
        else:
            if not payload["name"]:
                payload["name"] = self.odoo_record.name
            payload = {
                **payload,
                **{
                    "backend_id": backend_record.id,
                    "external_id": rate_id,
                },
            }
            self.env["odoo.res.currency.rate"].with_context(
                connector_no_export=True
            ).create(payload)


class ResCurrencyRate(models.Model):
    _inherit = "res.currency.rate"

    bind_ids = fields.One2many(
        comodel_name="odoo.res.currency.rate",
        inverse_name="odoo_id",
        string="Odoo Bindings",
    )


class ResCurrencyRateAdapter(Component):
    _name = "odoo.res.currency.rate.adapter"
    _inherit = "odoo.adapter"
    _apply_on = "odoo.res.currency.rate"
    _odoo_model = "res.currency.rate"
