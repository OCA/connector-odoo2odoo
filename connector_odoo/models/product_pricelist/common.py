# -*- coding: utf-8 -*-
# Copyright 2013-2017 Camptocamp SA
# © 2016 Sodexis
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from odoo import models, fields
from odoo.addons.component.core import Component


_logger = logging.getLogger(__name__)


class OdooProductPricelist(models.Model):
    _name = 'odoo.product.pricelist'
    _inherit = 'odoo.binding'
    _inherits = {'product.pricelist': 'odoo_id'}
    _description = 'Odoo Product Pricelist'

    odoo_parent_id = fields.Many2one(
        comodel_name='odoo.product.pricelist',
        string='Ext. Odoo Parent Pricelist',
        ondelete='cascade',
    )
    odoo_child_ids = fields.One2many(
        comodel_name='odoo.product.pricelist',
        inverse_name='odoo_parent_id',
        string='Ext. Odoo Child Categories',
    )


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
