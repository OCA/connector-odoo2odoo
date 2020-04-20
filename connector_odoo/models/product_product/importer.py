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


class ProductBatchImporter(Component):
    """ Import the Odoo Products.

    For every product category in the list, a delayed job is created.
    Import from a date
    """

    _name = "odoo.product.product.batch.importer"
    _inherit = "odoo.delayed.batch.importer"
    _apply_on = ["odoo.product.product"]

    def run(self, filters=None):
        """ Run the synchronization """
        external_ids = self.backend_adapter.search(filters)
        _logger.info(
            "search for odoo products %s returned %s", filters, external_ids
        )
        for external_id in external_ids:
            # TODO : get the categ parent_left and change the priority
            prod_id = self.backend_adapter.read(external_id)
            cat_id = self.backend_adapter.read(
                prod_id.categ_id.id, model="product.category"
            )
            job_options = {"priority": 15 + cat_id.parent_left or 0}
            self._import_record(external_id, job_options=job_options)


class ProductImportMapper(Component):
    _name = "odoo.product.product.import.mapper"
    _inherit = "odoo.import.mapper"
    _apply_on = ["odoo.product.product"]

    # TODO :     categ, special_price => minimal_price
    direct = [
        ("name", "name"),
        ("description", "description"),
        ("weight", "weight"),
        ("standard_price", "standard_price"),
        ("barcode", "barcode"),
        ("description_sale", "description_sale"),
        ("description_purchase", "description_purchase"),
        ("description_sale", "description_sale"),
        ("is_published", "website_published"),
        ("sale_ok", "sale_ok"),
        ("purchase_ok", "purchase_ok"),
        ("image", "image"),
    ]

    @mapping
    def uom_id(self, record):
        binder = self.binder_for('odoo.uom.uom')
        uom = binder.to_internal(record.uom_id.id, unwrap=True)
        return {"uom_id": uom.id}

    @mapping
    def uom_po_id(self, record):
        binder = self.binder_for('odoo.uom.uom')
        uom = binder.to_internal(record.uom_id.id, unwrap=True)
        return {"uom_po_id": uom.id}

    @mapping
    def price(self, record):
        return {"list_price": record.list_price}

    @mapping
    def default_code(self, record):
        code = record["default_code"]
        if not code:
            return {"default_code": "/"}
        return {"default_code": code}

    @mapping
    def type(self, record):
        res = {"type": "service"}
        if record["type"] == "product":
            res.update(type="consu")
        return res

    @only_create
    @mapping
    def odoo_id(self, record):
        match_field = u"default_code"
        if self.backend_record.matching_product_product:
            match_field = self.backend_record.matching_product_ch

        filters = ast.literal_eval(
            self.backend_record.local_product_domain_filter
        )
        if record[match_field]:
            filters.append((match_field, "=", record[match_field]))

        #         filters = ast.literal_eval(filters)
        prod_id = self.env["product.product"].search(filters)

        if len(prod_id) == 1:
            return {"odoo_id": prod_id.id}
        return {}

    @mapping
    def category(self, record):
        categ_id = record["categ_id"]
        binder = self.binder_for("odoo.product.category")

        cat = binder.to_internal(categ_id.id, unwrap=True)
        if not cat:
            raise MappingError(
                "The product category with odoo id %s is not imported."
                % cat.name
            )
        return {"categ_id": cat.id}


class ProductImporter(Component):
    _name = "odoo.product.product.importer"
    _inherit = "odoo.importer"
    _apply_on = ["odoo.product.product"]

    def _import_dependencies(self):
        """ Import the dependencies for the record"""
        # record = self.odoo_record
        # import related categories
        categ_id = self.odoo_record.categ_id
        self._import_dependency(categ_id.id, "odoo.product.category")

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
        binding = super(ProductImporter, self)._create(data)
        self.backend_record.add_checkpoint(binding)
        return binding

    def _after_import(self, binding):
        """ Hook called at the end of the import """
        pass
