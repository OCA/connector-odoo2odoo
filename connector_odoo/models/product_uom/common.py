# -*- coding: utf-8 -*-
# Copyright 2013-2017 Camptocamp SA
# © 2016 Sodexis
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import models, fields


class OdooProductUOM(models.Model):
    _name = 'odoo.product.uom'
    _inherit = 'odoo.binding'
    _inherits = {'product.uom': 'odoo_id'}
    _description = 'Odoo Product UOM'

    odoo_id = fields.Many2one(comodel_name='product.uom',
                              string='Product UOM',
                              required=True,
                              ondelete='restrict')
    


class ProductUOM(models.Model):
    _inherit = 'product.uom'
    
    bind_ids = fields.One2many(
        comodel_name='odoo.product.uom',
        inverse_name='odoo_id',
        string='Odoo Bindings',
    )

