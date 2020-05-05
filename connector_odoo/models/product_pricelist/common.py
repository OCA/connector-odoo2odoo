# -*- coding: utf-8 -*-
# Copyright 2013-2017 Camptocamp SA
# © 2016 Sodexis
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import ast
import logging
from odoo import models, fields
from odoo.addons.component.core import Component


_logger = logging.getLogger(__name__)


class OdooProductPricelist(models.Model):
    _name = 'odoo.product.pricelist'
    _inherit = 'odoo.binding'
    _inherits = {'product.pricelist': 'odoo_id'}
    _description = 'Odoo Product Pricelist'


class ProductPricelist(models.Model):
    _inherit = 'product.pricelist'

    bind_ids = fields.One2many(
        comodel_name='odoo.product.pricelist',
        inverse_name='odoo_id',
        string="Odoo Bindings",
    )


class ProductPricelistAdapter(Component):
    _name = 'odoo.product.pricelist.adapter'
    _inherit = 'odoo.adapter'
    _apply_on = 'odoo.product.pricelist'
    _odoo_model = 'product.pricelist'


class OdooProductPricelistItem(models.Model):
    _name = 'odoo.product.pricelist.item'
    _inherit = 'odoo.binding'
    _inherits = {'product.pricelist.item': 'odoo_id'}
    _description = 'Odoo Product Pricelist Item'


class ProductPricelistItem(models.Model):
    _inherit = 'product.pricelist.item'

    bind_ids = fields.One2many(
        comodel_name='odoo.product.pricelist.item',
        inverse_name='odoo_id',
        string="Odoo Bindings",
    )


class ProductPricelistItemAdapter(Component):
    _name = 'odoo.product.pricelist.item.adapter'
    _inherit = 'odoo.adapter'
    _apply_on = 'odoo.product.pricelist.item'
    _odoo_model = 'product.pricelist.item'

    def search(self, filters=None, model=None):
        """ Search records according to some criteria
        and returns a list of ids

        :rtype: list
        """
        if filters is None:
            filters = []
        ext_filter = ast.literal_eval(
            str(self.backend_record.external_product_pricelist_domain_filter)
        )
        filters += ext_filter
        return super(ProductPricelistItemAdapter, self).search(
            filters=filters, model=model
        )
