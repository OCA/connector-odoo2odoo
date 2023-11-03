# Copyright 2022 Greenice, S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import logging

from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping, only_create

_logger = logging.getLogger(__name__)


class ResCurrencyBatchImporter(Component):
    _name = "odoo.res.currency.batch.importer"
    _inherit = "odoo.delayed.batch.importer"
    _apply_on = ["odoo.res.currency"]

    def run(self, filters=None, force=False):
        """Run the synchronization"""
        external_ids = self.backend_adapter.search(
            filters,
        )
        _logger.info(
            "search for odoo Currency %s returned %s items", filters, len(external_ids)
        )
        for external_id in external_ids:
            job_options = {
                "priority": 15,
            }
            self._import_record(external_id, job_options=job_options)


class UomMapper(Component):
    _name = "odoo.res.currency.mapper"
    _inherit = "odoo.import.mapper"
    _apply_on = "odoo.res.currency"

    direct = [
        ("name", "name"),
        ("active", "active"),
        ("rounding", "rounding"),
        ("currency_unit_label", "currency_unit_label"),
        ("currency_subunit_label", "currency_subunit_label"),
        ("symbol", "symbol"),
        ("position", "position"),
        ("position", "position"),
    ]

    @only_create
    @mapping
    def check_res_currency_exists(self, record):
        res = {}
        currency_id = self.env["res.currency"].search(
            [
                ("name", "=", record.name),
                "|",
                ("active", "=", True),
                ("active", "=", False),
            ]
        )
        _logger.debug("Res currency found for %s : %s" % (record, currency_id))
        if len(currency_id) == 1:
            res.update({"odoo_id": currency_id.id})
        return res

    @mapping
    def decimal_places(self, record):
        if self.backend_record.version == "6.1":
            return {"decimal_places": record.accuracy}
        return {"decimal_places": record.decimal_places}


class CurrencyImporter(Component):
    """Import Odoo Currency"""

    _name = "odoo.res.currency.importer"
    _inherit = "odoo.importer"
    _apply_on = "odoo.res.currency"

    def _after_import(self, binding, force=False):
        _logger.info(
            "Importing Currency rates for external ID %s",
            self.external_id,
        )
        self.env["odoo.res.currency.rate"].with_delay().import_record(
            self.backend_record, self.external_id
        )
        return super()._after_import(binding, force)
