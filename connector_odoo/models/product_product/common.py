# -*- coding: utf-8 -*-
# Copyright 2013-2017 Camptocamp SA
# © 2016 Sodexis
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
import xmlrpclib
import ast

from collections import defaultdict

from odoo import models, fields, api
from odoo.addons.connector.exception import IDMissingInBackend
from odoo.addons.component.core import Component
from odoo.addons.component_event import skip_if
from odoo.addons.queue_job.job import job, related_action
# from ...components.backend_adapter import MAGENTO_DATETIME_FORMAT

_logger = logging.getLogger(__name__)


class OdooProductProduct(models.Model):
    _name = 'odoo.product.product'
    _inherit = 'odoo.binding'
    _inherits = {'product.product': 'odoo_id'}
    _description = 'External Odoo Product'
    
    @api.multi
    def name_get(self):
        result = []
        for op in self:
            name = '%s (Backend: %s)' % (op.odoo_id.display_name, op.backend_id.name)
            result.append((op.id, name))
            
        return result
        

    RECOMPUTE_QTY_STEP = 1000  # products at a time

    @job(default_channel='root.odoo')
    @api.multi
    def export_inventory(self, fields=None):
        """ Export the inventory configuration and quantity of a product. """
        self.ensure_one()
        with self.backend_id.work_on(self._name) as work:
            exporter = work.component(usage='product.inventory.exporter')
            return exporter.run(self, fields)

#     @api.multi
#     def recompute_odoo_qty(self):
#         """ Check if the quantity in the stock location configured
#         on the backend has changed since the last export.
# 
#         If it has changed, write the updated quantity on `odoo_qty`.
#         The write on `odoo_qty` will trigger an `on_record_write`
#         event that will create an export job.
# 
#         It groups the products by backend to avoid to read the backend
#         informations for each product.
#         """
#         # group products by backend
#         backends = defaultdict(set)
#         for product in self:
#             backends[product.backend_id].add(product.id)
# 
#         for backend, product_ids in backends.iteritems():
#             self._recompute_odoo_qty_backend(backend,
#                                                 self.browse(product_ids))
#         return True
# 
#     @api.multi
#     def _recompute_odoo_qty_backend(self, backend, products,
#                                        read_fields=None):
#         """ Recompute the products quantity for one backend.
# 
#         If field names are passed in ``read_fields`` (as a list), they
#         will be read in the product that is used in
#         :meth:`~._odoo_qty`.
# 
#         """
#         if backend.product_stock_field_id:
#             stock_field = backend.product_stock_field_id.name
#         else:
#             stock_field = 'virtual_available'
# 
#         location = self.env['stock.location']
#         if self.env.context.get('location'):
#             location = location.browse(self.env.context['location'])
#         else:
#             location = backend.warehouse_id.lot_stock_id
# 
#         product_fields = ['odoo_qty', stock_field]
#         if read_fields:
#             product_fields += read_fields
# 
#         self_with_location = self.with_context(location=location.id)
#         for chunk_ids in chunks(products.ids, self.RECOMPUTE_QTY_STEP):
#             records = self_with_location.browse(chunk_ids)
#             for product in records.read(fields=product_fields):
#                 new_qty = self._odoo_qty(product,
#                                             backend,
#                                             location,
#                                             stock_field)
#                 if new_qty != product['odoo_qty']:
#                     self.browse(product['id']).odoo_qty = new_qty

#     @api.multi
#     def _odoo_qty(self, product, backend, location, stock_field):
#         """ Return the current quantity for one product.
# 
#         Can be inherited to change the way the quantity is computed,
#         according to a backend / location.
# 
#         If you need to read additional fields on the product, see the
#         ``read_fields`` argument of :meth:`~._recompute_odoo_qty_backend`
# 
#         """
#         return product[stock_field]


class ProductProduct(models.Model):
    _inherit = 'product.product'

    bind_ids = fields.One2many(
        comodel_name='odoo.product.product',
        inverse_name='odoo_id',
        string='Odoo Bindings',
    )


class ProductProductAdapter(Component):
    _name = 'odoo.product.product.adapter'
    _inherit = 'odoo.adapter'
    _apply_on = 'odoo.product.product'

    _odoo_model = 'product.product'
    
    
    def search(self, filters=None, model=None,):
        """ Search records according to some criteria
        and returns a list of ids
 
        :rtype: list
        """
        if filters == None:
            filters = []
        ext_filter = ast.literal_eval(str(self.backend_record.external_product_domain_filter))
        filters += ext_filter
        return super(ProductProductAdapter, self).search( filters=filters, model=model,)
        
    
# 
#     def get_images(self, id, storeview_id=None):
#         return self._call('product_media.list', [int(id), storeview_id, 'id'])
# 
#     def read_image(self, id, image_name, storeview_id=None):
#         return self._call('product_media.info',
#                           [int(id), image_name, storeview_id, 'id'])
# 
#     def update_inventory(self, id, data):
#         # product_stock.update is too slow
#         return self._call('oerp_cataloginventory_stock_item.update',
#                           [int(id), data])


# class OdooBindingProductListener(Component):
#     _name = 'odoo.binding.product.product.listener'
#     _inherit = 'base.connector.listener'
#     _apply_on = ['odoo.product.product']
# 
#     # fields which should not trigger an export of the products
#     # but an export of their inventory
#     INVENTORY_FIELDS = ('manage_stock',
#                         'backorders',
#                         'odoo_qty',
#                         )
# 
#     @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
#     def on_record_write(self, record, fields=None):
#         if record.no_stock_sync:
#             return
#         inventory_fields = list(
#             set(fields).intersection(self.INVENTORY_FIELDS)
#         )
#         if inventory_fields:
#             record.with_delay(priority=20).export_inventory(
#                 fields=inventory_fields
#             )
