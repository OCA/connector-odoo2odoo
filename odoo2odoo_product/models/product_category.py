# -*- coding: utf-8 -*-
# Copyright 2018 ABF OSIELL <http://osiell.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp import models, fields


class ProductCategory(models.Model):
    _name = 'product.category'
    _inherit = ['product.category']

    odoo_bind_ids = fields.One2many(
        'odoo.product.category',
        inverse_name='odoo_id',
        string=u"Odoo Bindings",
        readonly=True)


class OdooProductCategory(models.Model):
    _name = 'odoo.product.category'
    _inherit = 'odoo.binding'
    _inherits = {'product.category': 'odoo_id'}

    odoo_id = fields.Many2one(
        'product.category',
        string=u"Category",
        required=True,
        ondelete='cascade')
