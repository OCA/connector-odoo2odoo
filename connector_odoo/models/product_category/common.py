# -*- coding: utf-8 -*-
# Copyright 2013-2017 Camptocamp SA
# © 2016 Sodexis
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
import xmlrpclib
from odoo import models, fields
from odoo.addons.connector.exception import IDMissingInBackend
from odoo.addons.component.core import Component


_logger = logging.getLogger(__name__)


class OdooProductCategory(models.Model):
    _name = 'odoo.product.category'
    _inherit = 'odoo.binding'
    _inherits = {'product.category': 'odoo_id'}
    _description = 'Odoo Product Category'

    odoo_parent_id = fields.Many2one(
        comodel_name='odoo.product.category',
        string='Ext. Odoo Parent Category',
        ondelete='cascade',
    )
    odoo_child_ids = fields.One2many(
        comodel_name='odoo.product.category',
        inverse_name='odoo_parent_id',
        string='Ext. Odoo Child Categories',
    )


class ProductCategory(models.Model):
    _inherit = 'product.category'

    bind_ids = fields.One2many(
        comodel_name='odoo.product.category',
        inverse_name='odoo_id',
        string="Odoo Bindings",
    )


class ProductCategoryAdapter(Component):
    _name = 'odoo.product.category.adapter'
    _inherit = 'odoo.adapter'
    _apply_on = 'odoo.product.category'
    _odoo_model = 'product.category'

