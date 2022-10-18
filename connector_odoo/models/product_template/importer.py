# Copyright 2013-2017 Camptocamp SA
# © 2016 Sodexis
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import logging

from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping
from odoo.addons.connector.exception import MappingError

_logger = logging.getLogger(__name__)


class ProductTemplateBatchImporter(Component):
    """Import the Odoo Products Template.

    For every product category in the list, a delayed job is created.
    Import from a date
    """

    _name = "odoo.product.template.batch.importer"
    _inherit = "odoo.delayed.batch.importer"
    _apply_on = ["odoo.product.template"]

    def run(self, filters=None, force=False):
        """Run the synchronization"""

        external_ids = self.backend_adapter.search(filters)
        _logger.info(
            "search for odoo products template %s returned %s items",
            filters,
            len(external_ids),
        )
        for external_id in external_ids:
            # TODO : get the parent_left of the category so that we change
            #   the priority
            prod_id = self.backend_adapter.read(external_id)
            cat_id = self.backend_adapter.read(
                prod_id.categ_id.id, model="product.category"
            )
            job_options = {"priority": 15 + cat_id.parent_left or 0}
            self._import_record(external_id, job_options=job_options)


class ProductTemplateImportMapper(Component):
    _name = "odoo.product.template.import.mapper"
    _inherit = "odoo.import.mapper"
    _apply_on = ["odoo.product.template"]

    # TODO :     categ, special_price => minimal_price
    direct = [
        ("description", "description"),
        ("weight", "weight"),
        ("standard_price", "standard_price"),
        ("barcode", "barcode"),
        ("description_sale", "description_sale"),
        ("description_purchase", "description_purchase"),
        ("sale_ok", "sale_ok"),
        ("purchase_ok", "purchase_ok"),
        ("type", "detailed_type"),
    ]

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
        if not hasattr(record, "default_code"):
            return {}
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
                "Can't find external category with odoo_id %s." % categ_id.odoo_id
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


class ProductTemplateImporter(Component):
    _name = "odoo.product.template.importer"
    _inherit = "odoo.importer"
    _apply_on = ["odoo.product.template"]

    def _import_dependencies(self, force=False):
        """Import the dependencies for the record"""
        uom_id = self.odoo_record.uom_id
        self._import_dependency(uom_id.id, "odoo.uom.uom", force=force)

        categ_id = self.odoo_record.categ_id
        self._import_dependency(categ_id.id, "odoo.product.category", force=force)
        return super()._import_dependencies(force=force)

    def _get_context(self, data):
        """Context for the creation"""
        return {"create_product_product": True}
