# -*- coding: utf-8 -*-
# Copyright 2018 ABF OSIELL <http://osiell.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp import models, fields


class ProductTemplate(models.Model):
    _name = 'product.template'
    _inherit = ['product.template']

    odoo_bind_ids = fields.One2many(
        'odoo.product.template',
        inverse_name='odoo_id',
        string=u"Odoo Bindings",
        readonly=True)


class OdooProductTemplate(models.Model):
    _name = 'odoo.product.template'
    _inherit = 'odoo.binding'
    _inherits = {'product.template': 'odoo_id'}

    odoo_id = fields.Many2one(
        'product.template',
        string=u"Product",
        required=True,
        ondelete='cascade')
