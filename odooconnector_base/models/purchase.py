# -*- coding: utf-8 -*-
# © 2015 Malte Jacobi (maljac @ github)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import logging
from openerp import models, fields
from openerp.addons.connector.unit.mapper import (ExportMapper, mapping)
from openerp.addons.connector.exception import MappingError
from ..unit.mapper import OdooExportMapChild
from ..unit.export_synchronizer import OdooExporter
from ..backend import oc_odoo

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


"""
E X P O R T
"""


@oc_odoo
class PurchaseOrder2SaleOrderExporter(OdooExporter):
    _model_name = ['odooconnector.purchase.order']

    def _get_remote_model(self):
        return 'sale.order'

    def _after_export(self, record_created):
        """
        (1) Set the partner id to the default intercompany partner
        (2) Get the SalesOrder name and set the partner_ref to it
        """
        assert self.binding_id

        data = {}

        purchase_order = self.model.browse(self.binding_id)
        po2so_partner = self.backend_record.po2so_intercompany_partner
        if po2so_partner:
            data = {
                'partner_id': po2so_partner.id,
                'ic_original_partner_id': purchase_order.partner_id.id
            }

        # try get the name of the create sales order in the IC system
        ic_so = self.backend_adapter.read(self.external_id,
                                          fields=['name'],
                                          model_name='sale.order')
        if ic_so:
            data['partner_ref'] = ic_so.get('name', None)

        if data:
            purchase_order.write(data)


@oc_odoo
class PurchaseOrder2SaleOrderExportMapper(ExportMapper):
    _model_name = ['odooconnector.purchase.order']
    _map_child_class = OdooExportMapChild

    # _direct = ['date_order']
    direct = [('date_order', 'date_order'), ]

    children = [
        ('order_line', 'order_line', 'odooconnector.purchase.order.line')
    ]

    @mapping
    def origin(self, record):
        return {
            'origin': 'IC:{}'.format(record.name)
        }

    @mapping
    def client_order_ref(self, record):
        return {
            'client_order_ref': 'IC:{}'.format(record.name)
        }

    @mapping
    def partner_id(self, record):
        # we have a default partner id for ourself in the intercompany system
        partner_id = self.backend_record.export_partner_id
        return {'partner_id': partner_id}

    @mapping
    def ic_supplier_id(self, record):
        ic_id = self.binder_for('odooconnector.res.partner').to_backend(
            record.partner_id.id,
            wrap=True
        )
        if not ic_id:
            raise MappingError('The partner has no binding for this backend')

        return {'ic_supplier_id': ic_id}


@oc_odoo
class PurchaseOrderLine2SaleOrderLineExportMapper(ExportMapper):
    _model_name = ['odooconnector.purchase.order.line']

    direct = [
        ('name', 'name'), ('price_unit', 'price_unit'),
        ('product_qty', 'product_uom_qty'),
    ]

    @mapping
    def product_id(self, record):
        ic_id = self.binder_for('odooconnector.product.product').to_backend(
            record.product_id.id,
            wrap=True
        )
        if ic_id:
            return {'product_id': ic_id}

    @mapping
    def product_uom(self, record):
        ic_id = self.binder_for('odooconnector.product.uom').to_backend(
            record.product_uom.id,
            wrap=True
        )
        if not ic_id:
            raise MappingError('The UoM has no binding for this backend')
        _logger.debug('Using Product UoM %s for %s and line %s',
                      ic_id, record.product_uom, record.id)
        return {'product_uom': ic_id}
