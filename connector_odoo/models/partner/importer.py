# -*- coding: utf-8 -*-
# Copyright 2013-2017 Camptocamp SA
# © 2016 Sodexis
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import ast
import logging

from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping, only_create
from odoo.addons.connector.exception import MappingError

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
        ("company_type", "company_type"),
        ("image", "image"),
    ]

    @mapping
    def state_id(self, record):
        state_id = False
        country_id = False
        if record.country_id:
            country_code = record.country_id.code
        else:
            country_code = 'CA'
        country = self.env["res.country"].search([
            ("code", "=", country_code),
        ])
        country_id = country.id
        if record.state_id:
            state = self.env["res.country.state"].search([
                ("code", "=", record.state_id.code),
                ("country_id", "=", country_id),
            ])
            state_id = state.id
        return {
            "state_id": state_id,
            "country_id": country_id,
        }

    @mapping
    def category(self, record):
        res = {"parent_id": False}
        parent = record.parent_id
        if parent:
            binder = self.binder_for("odoo.res.partner")

            bind_parent = binder.to_internal(parent.id, unwrap=True)
            if not bind_parent:
                raise MappingError(
                    "The parent partner with odoo id %s is not imported."
                    % parent.name
                )
            res.update(parent_id=bind_parent.id)
        return res

    @only_create
    @mapping
    def odoo_id(self, record):
        filters = ast.literal_eval(
            self.backend_record.local_partner_domain_filter
        )
        if record.ref or record.email:
            filters.extend([
                '|', ("ref", "=", record.ref),
                ("email", "=", record.email),
            ])
        partner = self.env["res.partner"].search(filters)

        if len(partner) == 1:
            return {"odoo_id": partner.id}
        return {}


class PartnerImporter(Component):
    _name = "odoo.res.partner.importer"
    _inherit = "odoo.importer"
    _apply_on = ["odoo.res.partner"]

    def _import_dependencies(self):
        """ Import the dependencies for the record"""
        # import parent
        if self.odoo_record.parent_id:
            self._import_dependency(
                self.odoo_record.parent_id.id, "odoo.res.partner")

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
