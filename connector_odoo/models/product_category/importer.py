# Copyright 2013-2017 Camptocamp SA
# © 2016 Sodexis
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import logging

from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping
from odoo.addons.connector.exception import MappingError

_logger = logging.getLogger(__name__)


class ProductCategoryBatchImporter(Component):
    """Import the Odoo Product Categories.

    For every product category in the list, a delayed job is created.
    A priority is set on the jobs according to their level to rise the
    chance to have the top level categories imported first.
    """

    _name = "odoo.product.category.batch.importer"
    _inherit = "odoo.delayed.batch.importer"
    _apply_on = ["odoo.product.category"]

    def run(self, filters=None, force=False):
        """Run the synchronization"""

        updated_ids = self.backend_adapter.search(filters)
        _logger.info(
            "search for odoo product categories %s returned %s items",
            filters,
            len(updated_ids),
        )
        base_priority = 10
        for cat in updated_ids:
            cat_id = self.backend_adapter.read(cat)
            job_options = {"priority": base_priority + cat_id.parent_left or 0}
            self._import_record(cat_id.id, job_options=job_options)


class ProductCategoryImporter(Component):
    _name = "odoo.product.category.importer"
    _inherit = "odoo.importer"
    _apply_on = ["odoo.product.category"]

    def _import_dependencies(self, force=False):
        """Import the dependencies for the record"""
        record = self.odoo_record
        # import parent category
        # the root category has a 0 parent_id
        if record.parent_id:
            self._import_dependency(record.parent_id.id, self.model, force=False)

    def _after_import(self, binding, force=False):
        """Hook called at the end of the import"""
        binding._parent_store_compute()
        return super()._after_import(binding, force)


class ProductCategoryImportMapper(Component):
    _name = "odoo.product.category.import.mapper"
    _inherit = "odoo.import.mapper"
    _apply_on = "odoo.product.category"

    direct = [("name", "name")]

    @mapping
    def parent_id(self, record):
        if not record.parent_id:
            return
        binder = self.binder_for()
        parent_binding = binder.to_internal(record.parent_id.id)

        if not parent_binding:
            raise MappingError(
                "The product category with "
                "Odoo id %s is not imported." % record.parent_id.id
            )

        parent = parent_binding.odoo_id
        return {"parent_id": parent.id, "odoo_parent_id": parent_binding.id}
