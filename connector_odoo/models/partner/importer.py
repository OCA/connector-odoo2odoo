# -*- coding: utf-8 -*-
# Copyright 2013-2017 Camptocamp SA
# © 2016 Sodexis
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import logging

from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping

_logger = logging.getLogger(__name__)


class PartnerBatchImporter(Component):
    """ Import the Odoo Partner.

    For every partner in the list, a delayed job is created.
    Import from a date
    """

    _name = "odoo.res.partner.batch.importer"
    _inherit = "odoo.delayed.batch.importer"
    _apply_on = ["odoo.res.partner"]

    def run(self, filters=None):
        """ Run the synchronization """

        external_ids = self.backend_adapter.search(filters)
        _logger.info(
            "search for odoo partner %s returned %s", filters, external_ids
        )
        for external_id in external_ids:
            job_options = {"priority": 15}
            self._import_record(external_id, job_options=job_options)


class PartnerImportMapper(Component):
    _name = "odoo.res.partner.import.mapper"
    _inherit = "odoo.import.mapper"
    _apply_on = ["odoo.res.partner"]

    # TODO :     categ, special_price => minimal_price
    direct = [
        ("name", "name"),
        ("street", "street"),
        ("street2", "street2"),
        ("city", "city"),
        ("website", "website"),
        ("phone", "phone"),
        ("mobile", "mobile"),
        ("lang", "lang"),
        ("customer", "customer"),
        ("supplier", "supplier"),
        ("ref", "ref"),
        ("comment", "comment"),
        ("image", "image"),
    ]

    @mapping
    def state_id(self, record):
        state_id = False
        if record.state_id:
            state = self.env["res.country.state"].search(
                [("code", "=", record.state_id.code)]
            )
            state_id = state.id
        return {"state_id": state_id}

    @mapping
    def country_id(self, record):
        country_id = False
        if record.country_id:
            country = self.env["res.country"].search(
                [("code", "=", record.country_id.code)]
            )
            country_id = country.id
        return {"country_id": country_id}


class PartnerImporter(Component):
    _name = "odoo.product.template.importer"
    _inherit = "odoo.importer"
    _apply_on = ["odoo.product.template"]

    def _import_dependencies(self):
        """ Import the dependencies for the record"""
        # record = self.odoo_record
        # import related categories
        # categ_id = self.odoo_record.categ_id
        # self._import_dependency(categ_id.id, "odoo.product.category")

    def _must_skip(self):
        """ Hook called right after we read the data from the backend.

        If the method returns a message giving a reason for the
        skipping, the import will be interrupted and the message
        recorded in the job (if the import is called directly by the
        job, not by dependencies).

        If it returns None, the import will continue normally.

        :returns: None | str | unicode
        """

    def _create(self, data):
        binding = super(PartnerImporter, self)._create(data)
        self.backend_record.add_checkpoint(binding)
        return binding

    def _after_import(self, binding):
        """ Hook called at the end of the import """
