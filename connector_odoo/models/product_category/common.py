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
# 
#     def _call(self, method, arguments):
#         try:
#             return super(ProductCategoryAdapter, self)._call(method, arguments)
#         except xmlrpclib.Fault as err:
#             # 101 is the error in the Odoo API
#             # when the category does not exist
#             if err.faultCode == 102:
#                 raise IDMissingInBackend
#             else:
#                 raise
# 
#     def search(self, filters=None, from_date=None, to_date=None):
#         """ Search records according to some criteria and return a
#         list of ids
# 
#         :rtype: list
#         """
#         if filters is None:
#             filters = {}
# 
#         dt_fmt = MAGENTO_DATETIME_FORMAT
#         if from_date is not None:
#             filters.setdefault('updated_at', {})
#             # updated_at include the created records
#             filters['updated_at']['from'] = from_date.strftime(dt_fmt)
#         if to_date is not None:
#             filters.setdefault('updated_at', {})
#             filters['updated_at']['to'] = to_date.strftime(dt_fmt)
# 
#         return self._call('oerp_catalog_category.search',
#                           [filters] if filters else [{}])
# 
#     def read(self, id, storeview_id=None, attributes=None):
#         """ Returns the information of a record
# 
#         :rtype: dict
#         """
#         return self._call('%s.info' % self._odoo_model,
#                           [int(id), storeview_id, attributes])
# 
#     def tree(self, parent_id=None, storeview_id=None):
#         """ Returns a tree of product categories
# 
#         :rtype: dict
#         """
#         def filter_ids(tree):
#             children = {}
#             if tree['children']:
#                 for node in tree['children']:
#                     children.update(filter_ids(node))
#             category_id = {tree['category_id']: children}
#             return category_id
#         if parent_id:
#             parent_id = int(parent_id)
#         tree = self._call('%s.tree' % self._odoo_model,
#                           [parent_id, storeview_id])
#         return filter_ids(tree)
# 
#     def move(self, categ_id, parent_id, after_categ_id=None):
#         return self._call('%s.move' % self._odoo_model,
#                           [categ_id, parent_id, after_categ_id])
# 
#     def get_assigned_product(self, categ_id):
#         return self._call('%s.assignedProducts' % self._odoo_model,
#                           [categ_id])
# 
#     def assign_product(self, categ_id, product_id, position=0):
#         return self._call('%s.assignProduct' % self._odoo_model,
#                           [categ_id, product_id, position, 'id'])
# 
#     def update_product(self, categ_id, product_id, position=0):
#         return self._call('%s.updateProduct' % self._odoo_model,
#                           [categ_id, product_id, position, 'id'])
# 
#     def remove_product(self, categ_id, product_id):
#         return self._call('%s.removeProduct' % self._odoo_model,
#                           [categ_id, product_id, 'id'])
