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


class OdooProductTemplate(models.Model):
    _name = "odoo.product.template"
    _inherit = "odoo.binding"
    _inherits = {"product.template": "odoo_id"}
    _description = "External Odoo Product Template"

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


class ProductTemplate(models.Model):
    _inherit = "product.template"

    bind_ids = fields.One2many(
        comodel_name="odoo.product.template",
        inverse_name="odoo_id",
        string="Odoo Bindings",
    )


class ProductTemplateAdapter(Component):
    _name = "odoo.product.template.adapter"
    _inherit = "odoo.adapter"
    _apply_on = "odoo.product.template"

    _odoo_model = "product.template"

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
        return super(ProductTemplateAdapter, self).search(
            filters=filters, model=model
        )
