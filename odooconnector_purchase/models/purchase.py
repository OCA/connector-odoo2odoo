# -*- coding: utf-8 -*-
# © 2015 Malte Jacobi (maljac @ github)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import logging
from openerp import models, fields
from openerp.addons.odooconnector_base.backend import oc_odoo
from openerp.addons.odooconnector_base.unit.backend_adapter import OdooAdapter
from openerp.addons.odooconnector_base.unit.binder import OdooModelBinder

_logger = logging.getLogger(__name__)


"""

Purchase
========

All implementations specific related to the export / import / mapping etc.
of purchase order objects.

"""


class OdooConnectorPurchaseOrder(models.Model):
    _name = 'odooconnector.purchase.order'
    _inherit = 'odooconnector.binding'
    _inherits = {'purchase.order': 'openerp_id'}
    _description = 'Odoo Connector Purchase Order'

    openerp_id = fields.Many2one(
        comodel_name='purchase.order',
        string='Purchase Order',
        required=True,
        ondelete='restrict'
    )


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    oc_bind_ids = fields.One2many(
        comodel_name='odooconnector.purchase.order',
        inverse_name='openerp_id',
        string='Odoo Binding'
    )


class OdooConnectorPurchaseOrderLine(models.Model):
    _name = 'odooconnector.purchase.order.line'
    _inherit = 'odooconnector.binding'
    _inherits = {'purchase.order.line': 'openerp_id'}
    _description = 'Odoo Connector Purchase Order Line'

    openerp_id = fields.Many2one(
        comodel_name='purchase.order.line',
        string='Purchase Order Line',
        required=True,
        ondelete='restrict'
    )


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    oc_bind_ids = fields.One2many(
        comodel_name='odooconnector.purchase.order.line',
        inverse_name='openerp_id',
        string='Odoo Binding'
    )


@oc_odoo
class OdooModelBinderPurchase(OdooModelBinder):
    _model_name = [
        'odooconnector.purchase.order',
    ]


@oc_odoo
class OdooAdapterPurchase(OdooAdapter):
    _model_name = [
        'odooconnector.purchase.order'
    ]
