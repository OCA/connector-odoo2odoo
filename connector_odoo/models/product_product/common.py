# -*- coding: utf-8 -*-
# Copyright 2013-2017 Camptocamp SA
# © 2016 Sodexis
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import ast
import logging

from odoo import api, fields, models
from odoo.addons.component.core import Component
from odoo.addons.queue_job.job import job

_logger = logging.getLogger(__name__)


class OdooProductProduct(models.Model):
    _name = "odoo.product.product"
    _inherit = "odoo.binding"
    _inherits = {"product.product": "odoo_id"}
    _description = "External Odoo Product"

    @api.multi
    def name_get(self):
        result = []
        for op in self:
            name = "{} (Backend: {})".format(
                op.odoo_id.display_name,
                op.backend_id.display_name,
            )
            result.append((op.id, name))
        return result

    RECOMPUTE_QTY_STEP = 1000  # products at a time

    @job(default_channel="root.odoo")
    @api.multi
    def export_inventory(self, fields=None):
        """ Export the inventory configuration and quantity of a product. """
        self.ensure_one()
        with self.backend_id.work_on(self._name) as work:
            exporter = work.component(usage="product.inventory.exporter")
            return exporter.run(self, fields)


class ProductProduct(models.Model):
    _inherit = "product.product"

    bind_ids = fields.One2many(
        comodel_name="odoo.product.product",
        inverse_name="odoo_id",
        string="Odoo Bindings",
    )

    @api.multi
    def get_remote_qty_available(self, location=False):
        res = {}
        for product in self:
            context = {}
            bindings = product.bind_ids or product.product_tmpl_id.bind_ids
            if not bindings:
                continue
            # FIXME: Not sure how we should specify one
            binding = bindings[0]
            location = location or self._context.get('location', False)
            if location:
                context.update(location=location)
            with binding.backend_id.work_on('odoo.product.product') as work:
                adapter = work.component(
                    usage='record.importer').backend_adapter
                res[product.id] = adapter.read(
                    binding.external_id, context=context
                ).qty_available
        return res


class ProductProductAdapter(Component):
    _name = "odoo.product.product.adapter"
    _inherit = "odoo.adapter"
    _apply_on = "odoo.product.product"

    _odoo_model = "product.product"

    def search(self, filters=None, model=None):
        """ Search records according to some criteria
        and returns a list of ids
        :rtype: list
        """
        if filters is None:
            filters = []
        ext_filter = ast.literal_eval(
            str(self.backend_record.external_product_domain_filter)
        )
        filters += ext_filter
        return super(ProductProductAdapter, self).search(
            filters=filters, model=model
        )
