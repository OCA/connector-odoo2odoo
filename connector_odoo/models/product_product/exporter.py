# Copyright 2013-2017 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import ast
import logging

from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping, only_create
from odoo.addons.connector.exception import MappingError

# pylint: disable=odoo-addons-relative-import
from odoo.addons.connector_odoo.components.mapper import field_by_lang

_logger = logging.getLogger(__name__)


class BatchProductExporter(Component):
    _name = "odoo.product.product.batch.exporter"
    _inherit = "odoo.delayed.batch.exporter"
    _apply_on = ["odoo.product.product"]
    _usage = "batch.exporter"

    def run(self, filters=None, force=False):
        loc_filter = ast.literal_eval(self.backend_record.local_product_domain_filter)
        filters += loc_filter
        prod_ids = self.env["product.product"].search(filters)
        o_ids = self.env["odoo.product.product"].search(
            [("backend_id", "=", self.backend_record.id)]
        )
        o_prod_ids = self.env["product.product"].search(
            [("id", "in", [o.odoo_id.id for o in o_ids])]
        )
        to_bind = prod_ids - o_prod_ids
        for p in to_bind:
            self.env["odoo.product.product"].create(
                {
                    "odoo_id": p.id,
                    "external_id": 0,
                    "backend_id": self.backend_record.id,
                }
            )
        bind_ids = self.env["odoo.product.product"].search(
            [
                ("odoo_id", "in", [p.id for p in prod_ids]),
                ("backend_id", "=", self.backend_record.id),
            ]
        )
        for prod in bind_ids:
            job_options = {"max_retries": 0, "priority": 15}
            self._export_record(prod, job_options=job_options)


class OdooProductExporter(Component):
    _name = "odoo.product.product.exporter"
    _inherit = "odoo.exporter"
    _apply_on = ["odoo.product.product"]

    def _export_dependencies(self):
        categ_ids = self.binding.categ_id.bind_ids
        categ_id = self.env["odoo.product.category"]
        if categ_ids:
            categ_id = categ_ids.filtered(lambda c: c.backend_id == self.backend_record)
        if not categ_id:
            categ_id = self.env["odoo.product.category"].create(
                {
                    "odoo_id": self.binding.categ_id.id,
                    "external_id": 0,
                    "backend_id": self.backend_record.id,
                }
            )

        cat = self.binder.to_external(categ_id, wrap=False)
        if not cat:
            # Export the parent ID if it doesn't exists
            # TODO: Check if test is necessary
            # (export dependency probably update the record)
            #  categ_id.with_delay().export_record()
            #  self.env['product.category'].export_record(
            #      self.backend_record, external_id)
            self._export_dependency(categ_id, "odoo.product.category")

    def _create_data(self, map_record, fields=None, **kwargs):
        """Get the data to pass to :py:meth:`_create`"""
        datas = ast.literal_eval(self.backend_record.default_product_export_dict)
        cp_datas = map_record.values(for_create=True, fields=fields, **kwargs)
        # Combine default values with the computed ones
        datas.update(cp_datas)
        return datas


class ProductExportMapper(Component):
    _name = "odoo.product.product.export.mapper"
    _inherit = "odoo.export.mapper"
    _apply_on = ["odoo.product.product"]

    # TODO: categ, special_price => minimal_price
    direct = [
        (field_by_lang("name"), "name"),
        (field_by_lang("description"), "description"),
        (field_by_lang("description_sale"), "description_sale"),
        (field_by_lang("description_purchase"), "description_purchase"),
        (field_by_lang("description_sale"), "description_sale"),
        ("weight", "weight"),
        ("standard_price", "standard_price"),
        ("barcode", "barcode"),
        ("type", "type"),
        ("sale_ok", "sale_ok"),
        ("purchase_ok", "purchase_ok"),
        ("image", "image"),
    ]

    def get_product_by_match_field(self, record):
        match_field = "default_code"
        filters = []
        if self.backend_record.matching_product_product:
            match_field = self.backend_record.matching_product_ch
        filters = ast.literal_eval(self.backend_record.external_product_domain_filter)
        if record[match_field]:
            filters.append((match_field, "=", record[match_field]))
        adapter = self.component(usage="record.exporter").backend_adapter
        prod_id = adapter.search(filters)
        if len(prod_id) == 1:
            return prod_id[0]
        return False

    @mapping
    def uom_id(self, record):
        binder = self.binder_for("odoo.product.uom")
        uom_id = binder.wrap_binding(record.uom_id)
        return {"uom_id": uom_id, "uom_po_id": uom_id}

    @mapping
    def price(self, record):
        return {"list_price": record.list_price}

    @mapping
    def default_code(self, record):
        code = record["default_code"]
        if not code:
            # Prevent not null values
            return {"default_code": "/"}
        return {"default_code": code}

    @only_create
    @mapping
    def odoo_id(self, record):
        external_id = self.get_product_by_match_field(record)
        if external_id:
            return {"external_id": external_id}

    @mapping
    def category(self, record):
        categ_id = record["categ_id"]
        binder = self.binder_for("odoo.product.category")
        # binder.model = 'odoo.product.category'
        cat = binder.wrap_binding(categ_id)
        if not cat:
            raise MappingError(
                "The product category with odoo id %s is not available." % categ_id
            )
        return {"categ_id": cat}
