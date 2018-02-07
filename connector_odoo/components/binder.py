# -*- coding: utf-8 -*-
# © 2013 Guewen Baconnier,Camptocamp SA,Akretion
# © 2016 Sodexis
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import Component


class OdooModelBinder(Component):
    """ Bind records and give odoo/odoo ids correspondence

    Binding models are models called ``odoo.{normal_model}``,
    like ``odoo.res.partner`` or ``odoo.product.product``.
    They are ``_inherits`` of the normal models and contains
    the Odoo ID, the ID of the Odoo Backend and the additional
    fields belonging to the Odoo instance.
    """
    _name = 'odoo.binder'
    _inherit = ['base.binder', 'base.odoo.connector']
    _apply_on = [
        'odoo.product.uom',
        'odoo.product.attribute',
        'odoo.product.attribute.value',
#         'odoo.res.partner',
#         'odoo.res.partner.category',
#         'odoo.product.category',
#         'odoo.product.product',
#         'odoo.stock.picking',
#         'odoo.sale.order',
#         'odoo.sale.order.line',
#         'odoo.account.invoice',
    ]
