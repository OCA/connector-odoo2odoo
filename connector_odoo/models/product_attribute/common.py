# -*- coding: utf-8 -*-
# Copyright 2013-2017 Camptocamp SA
# © 2016 Sodexis
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import models, fields
from odoo.addons.component.core import Component

class OdooProductAttribute(models.Model):
    _name = 'odoo.product.attribute'
    _inherit = ['odoo.binding', ]
    _inherits = {'product.attribute': 'odoo_id'}
    _description = 'Odoo Product Attribute'

class ProductAttribute(models.Model):
    _inherit = 'product.attribute'
    
    bind_ids = fields.One2many(
        comodel_name='odoo.product.attribute',
        inverse_name='odoo_id',
        string='Odoo Bindings',
    )

class ProductAttributeAdapter(Component):
    _name = 'odoo.product.attribute.adapter'
    _inherit = 'odoo.adapter'
    _apply_on = 'odoo.product.attribute'
    _odoo_model = 'product.attribute'
