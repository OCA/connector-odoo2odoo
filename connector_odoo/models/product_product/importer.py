# Copyright 2013-2017 Camptocamp SA
# © 2016 Sodexis
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import logging

from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping, only_create
from odoo.addons.connector.exception import MappingError

_logger = logging.getLogger(__name__)


class ProductBatchImporter(Component):
    """Import the Odoo Products.

    For every product category in the list, a delayed job is created.
    Import from a date
    """

    _name = "odoo.product.product.batch.importer"
    _inherit = "odoo.delayed.batch.importer"
    _apply_on = ["odoo.product.product"]

    def run(self, filters=None, force=False):
        """Run the synchronization"""
        external_ids = self.backend_adapter.search(filters)
        _logger.info(
            "search for odoo products %s returned %s items", filters, len(external_ids)
        )
        for external_id in external_ids:
            # TODO : get the categ parent_left and change the priority
            prod_id = self.backend_adapter.read(external_id)
            cat_id = self.backend_adapter.read(
                prod_id.categ_id.id, model="product.category"
            )
            job_options = {"priority": 15 + cat_id.parent_left or 0}
            self._import_record(external_id, job_options=job_options, force=force)


class ProductImportMapper(Component):
    _name = "odoo.product.product.import.mapper"
    _inherit = "odoo.import.mapper"
    _apply_on = ["odoo.product.product"]

    direct = [
        ("description", "description"),
        ("weight", "weight"),
        ("volume", "volume"),
        ("standard_price", "standard_price"),
        ("description_sale", "description_sale"),
        ("description_purchase", "description_purchase"),
        ("description_sale", "description_sale"),
        ("sale_ok", "sale_ok"),
        ("purchase_ok", "purchase_ok"),
        ("type", "detailed_type"),
    ]

    @only_create
    @mapping
    def odoo_id(self, record):
        # If product was imported or created yet (manually or by another connector)
        binder = self.binder_for("odoo.product.product")
        if binder.to_internal(record.id, unwrap=True):
            return {"odoo_id": record.id}
        product_id = self.env["product.product"].search(
            [("default_code", "=", record.default_code)]
        )
        if product_id:
            return {"odoo_id": product_id.id}
        barcode = self.barcode(record)["barcode"]
        if barcode:
            product_id = self.env["product.product"].search([("barcode", "=", barcode)])
            if product_id:
                return {"odoo_id": product_id.id}
        return {}

    @mapping
    def company_id(self, record):
        return {"company_id": self.env.user.company_id.id}

    @mapping
    def uom_id(self, record):
        binder = self.binder_for("odoo.uom.uom")
        uom = binder.to_internal(record.uom_id.id, unwrap=True)
        return {"uom_id": uom.id}

    @mapping
    def uom_po_id(self, record):
        binder = self.binder_for("odoo.uom.uom")
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
    def name(self, record):
        if not hasattr(record, "name"):
            return {}
        name = record["name"]
        if not name:
            return {"name": "/"}
        return {"name": name}

    @mapping
    def category(self, record):
        categ_id = record["categ_id"]
        binder = self.binder_for("odoo.product.category")

        cat = binder.to_internal(categ_id.id, unwrap=True)
        if not cat:
            raise MappingError(
                "Can't find external category with odoo_id %s." % categ_id.id
            )
        return {"categ_id": cat.id}

    @mapping
    def is_published(self, record):
        is_published = False
        if hasattr(record, "website_published"):
            is_published = record["website_published"]
        elif hasattr(record, "is_published"):
            is_published = record["is_published"]
        else:
            return {}
        return {"is_published": is_published}

    @mapping
    def image(self, record):
        if self.backend_record.version in (
            "6.1",
            "7.0",
            "8.0",
            "9.0",
            "10.0",
            "11.0",
            "12.0",
        ):
            return {"image_1920": record.image if hasattr(record, "image") else False}
        else:
            return {"image_1920": record.image_1920}

    @mapping
    def barcode(self, record):
        barcode = False
        if hasattr(record, "barcode"):
            barcode = record["barcode"]
        elif hasattr(record, "ean13"):
            barcode = record["ean13"]
        return {"barcode": barcode}

    @mapping
    def product_tmpl_id(self, record):
        if self.backend_record.work_with_variants and record.product_tmpl_id:
            binder = self.binder_for("odoo.product.template")
            template_id = binder.to_internal(record.product_tmpl_id.id, unwrap=True)
            if template_id:
                return {"product_tmpl_id": template_id.id}
        return {}


class ProductImporter(Component):
    _name = "odoo.product.product.importer"
    _inherit = "odoo.importer"
    _apply_on = ["odoo.product.product"]

    def _import_dependencies(self, force=False):
        if self.backend_record.work_with_variants:
            product_tmpl_id = self.odoo_record.product_tmpl_id
            binder = self.binder_for("odoo.product.template")
            odoo_product_tmpl_id = binder.to_internal(product_tmpl_id.id, unwrap=True)
            if not odoo_product_tmpl_id:
                self._import_dependency(
                    product_tmpl_id.id, "odoo.product.template", force=force
                )

        uom_id = self.odoo_record.uom_id
        self._import_dependency(uom_id.id, "odoo.uom.uom", force=force)

        categ_id = self.odoo_record.categ_id
        self._import_dependency(categ_id.id, "odoo.product.category", force=force)

        return super()._import_dependencies(force=force)

    def _after_import(self, binding, force=False):
        attachment_model = self.work.odoo_api.api.get("ir.attachment")
        attachment_ids = attachment_model.search(
            [
                ("res_model", "=", "product.product"),
                ("res_id", "=", self.odoo_record.id),
            ],
            order="id",
        )
        total = len(attachment_ids)
        _logger.info(
            "{} Attachment found for external product {}".format(
                total, self.odoo_record.id
            )
        )
        for attachment_id in attachment_ids:
            self.env["odoo.ir.attachment"].with_delay().import_record(
                self.backend_record, attachment_id
            )
        return super()._after_import(binding, force)
