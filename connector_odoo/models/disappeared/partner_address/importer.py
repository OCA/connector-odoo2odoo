# Copyright 2022 Greenice, S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)
import logging

from odoo.addons.component.core import Component

_logger = logging.getLogger(__name__)


class PartnerAddressDisappearedBatchImporter(Component):
    """Import the Odoo Partner from Address (OpenERP Model deprecated).

    For every partner address in the list, a delayed job is created.
    Import from a date
    """

    _name = "odoo.res.partner.address.disappeared.batch.importer"
    _inherit = "odoo.delayed.batch.importer"
    _apply_on = ["odoo.res.partner.address.disappeared"]

    def run(self, filters=None, force=False):
        """Run the synchronization"""

        external_ids = self.backend_adapter.search(filters)
        _logger.info(
            "search for odoo partner address %s returned %s items",
            filters,
            len(external_ids),
        )
        for external_id in external_ids:
            job_options = {"priority": 15}
            self._import_record(external_id, job_options=job_options, force=force)


class PartnerAddressDisappearedImporter(Component):
    _name = "odoo.res.partner.address.disappeared.importer"
    _inherit = "odoo.importer"
    _apply_on = ["odoo.res.partner.address.disappeared"]

    def _init_import(self, binding, external_id):
        address_model = self.work.odoo_api.api.get("res.partner.address")
        address_ids = address_model.search(
            [("partner_id", "=", external_id)], order="id"
        )
        total = len(address_ids)
        _logger.info(
            "{} Addresses found for external partner {}".format(total, external_id)
        )
        if address_ids:
            i = 0
            for address_id in address_ids:
                # Creating new jobs are needed to avoid to maintain connection open
                # in large number of records
                # Jobs function only can be on models.Model, not in this class
                i += 1
                _logger.info(
                    "Sending address {} of {} to be processed as a new job".format(
                        i, total
                    )
                )
                self.env[
                    "odoo.res.partner.address.disappeared"
                ].with_delay().import_address(
                    self.backend_record, address_id, external_id
                )
        super()._init_import(binding, external_id)
        return False
