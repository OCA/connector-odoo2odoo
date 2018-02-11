# -*- coding: utf-8 -*-
# Copyright 2013-2017 Camptocamp SA
# © 2016 Sodexis
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import models, fields
from odoo.addons.component.core import Component

class OdooProductUOM(models.Model):
    _name = 'odoo.product.uom'
    _inherit = ['odoo.binding', ]
    _inherits = {'product.uom': 'odoo_id'}
    _description = 'Odoo Product UOM'
    
    """
    Product UOM are not fully managed with dependecies etc.
    User has the responsability to check the names are the same in
    both instances
    """

class ProductUoM(models.Model):
    _inherit = 'product.uom'
    
    bind_ids = fields.One2many(
        comodel_name='odoo.product.uom',
        inverse_name='odoo_id',
        string='Odoo Bindings',
    )



class ProductUoMAdapter(Component):
    _name = 'odoo.product.uom.adapter'
    _inherit = 'odoo.adapter'
    _apply_on = 'odoo.product.uom'
    _odoo_model = 'product.uom'
