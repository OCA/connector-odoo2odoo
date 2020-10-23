# -*- coding: utf-8 -*-
# Copyright 2013-2017 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import logging

from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping, only_create

_logger = logging.getLogger(__name__)


class BatchProductCategoryExporter(Component):
    _name = "odoo.product.category.batch.exporter"
    _inherit = "odoo.delayed.batch.exporter"
    _apply_on = ["odoo.product.category"]
    _usage = "batch.exporter"

    def run(self, filters=None):
        filters += [("backend_id", "=", self.backend_record.id)]
        prod_ids = self.env["odoo.product.category"].search(filters)
        for prod in prod_ids:
            job_options = {
                "max_retries": 0,
                "priority": 5 + prod.odoo_id.parent_left,
            }
            self._export_record(prod, job_options=job_options)


class OdooProductCategoryExporter(Component):
    _name = "odoo.product.category.exporter"
    _inherit = "odoo.exporter"
    _apply_on = ["odoo.product.category"]

    def _export_dependencies(self):
        if not self.binding.parent_id:
            return
        parent_ids = self.binding.parent_id.bind_ids
        parent_id = self.env["odoo.product.category"]
        if parent_ids:
            parent_id = parent_ids.filtered(
                lambda c: c.backend_id == self.backend_record
            )
        if not parent_id:
            parent_id = self.env["odoo.product.category"].create(
                {
                    "odoo_id": self.binding.parent_id.id,
                    "external_id": 0,
                    "backend_id": self.backend_record.id,
                }
            )

        cat = self.binder.to_external(parent_id, wrap=False)
        if not cat:
            # Export the parent ID if it doesn't exists
            # TODO: Check if test is necessary
            #  (export dependency probably update the record)
            self._export_dependency(parent_id, self.model)


class ProductExportCategoryMapper(Component):
    _name = "odoo.product.category.export.mapper"
    _inherit = "odoo.export.mapper"
    _apply_on = ["odoo.product.category"]

    # TODO: categ, special_price => minimal_price
    direct = [("name", "name"), ("type", "type")]

    def get_parent_categ(self, record):
        parent = record["parent_id"]
        parent_ids = parent.bind_ids
        parent_id = parent_ids.filtered(
            lambda c: c.backend_id == self.backend_record
        )
        binder = self.binder_for("odoo.product.category")
        cat = False
        if parent_id:
            cat = binder.to_external(parent_id, wrap=False)
        return cat

    @only_create
    @mapping
    def odoo_id(self, record):
        cat = self.get_parent_categ(record)
        categ_ids = []
        domain = [("name", "=", record["name"])]
        if cat:
            domain.append(("parent_id", "=", cat))
        adapter = self.component(usage="record.exporter").backend_adapter
        categ_ids = adapter.search(domain)
        if len(categ_ids) == 1:
            return {"external_id": categ_ids[0]}
        return {}

    @mapping
    def parent_id(self, record):
        cat = self.get_parent_categ(record)
        if cat:
            return {"parent_id": cat}
