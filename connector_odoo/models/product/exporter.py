# -*- coding: utf-8 -*-
# Copyright 2013-2017 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import ast
import odoo
import logging

from odoo import _
from odoo.addons.component.core import Component
from odoo.addons.queue_job.exception import NothingToDoJob
from odoo.addons.connector.components.mapper import mapping, only_create
from odoo.addons.connector.exception import MappingError, InvalidDataError

_logger = logging.getLogger(__name__)

class BatchProductExporter(Component):
    _name = 'odoo.product.product.batch.exporter'
    _inherit = 'odoo.delayed.batch.exporter'
    _apply_on = ['odoo.product.product']
    _usage = 'batch.exporter'


    def run(self, filters=None):        
        ext_filter = ast.literal_eval(self.backend_record.external_product_domain_filter)
        filters += ext_filter
        filters += [('backend_id', '=', self.backend_record.id)]
        
        prod_ids = self.env['odoo.product.product'].search(filters)
        for prod in prod_ids:
            job_options = {
                'max_retries': 0,
                'priority': 5,
            }
            self._export_record(prod, job_options=job_options)
    

class OdooProductExporter(Component):
    _name = 'odoo.product.product.exporter'
    _inherit = 'odoo.exporter'
    _apply_on = ['odoo.product.product']
    
    
    def _export_dependency(self, relation, binding_model,
                           component_usage='record.exporter',
                           binding_field='odoo_bind_ids',
                           binding_extra_vals=None):
        _logger.debug("TODO:\nExport dependency : %s" % binding_model)
        
    def _export_dependencies(self):
        _logger.debug("TODO: Export dependencies")
        
        self._export_dependency(False,'odoo.product.category')

    
#     def run(self, binding):
#         """
#         Export the products to Odoo
#         """
#         if binding.external_id > 0 :
#             
#             return _('Already exported')
#         
#         self.binder.bind(external_id, binding)
         


class ProductExportMapper(Component):
    _name = 'odoo.product.product.export.mapper'
    _inherit = 'odoo.export.mapper'
    _apply_on = ['odoo.product.product']

    # TODO :     categ, special_price => minimal_price
    direct = [('name', 'name'),
              ('description', 'description'),
              ('weight', 'weight'),
              ('standard_price', 'standard_price'),
              ('barcode', 'barcode'),              
              ('type', 'type'),
              ('description_sale', 'description_sale'),                            
              ('description_purchase', 'description_purchase'),               
              ('description_sale', 'description_sale'),               
              ('sale_ok', 'sale_ok'),               
              ('purchase_ok', 'purchase_ok'),     
              ('image', 'image'),     
                        
              ]

#     @mapping
#     def is_active(self, record):
#         """Check if the product is active in Odoo
#         and set active flag in OpenERP
#         status == 1 in Odoo means active"""
#         return {'active': (record.get('status') == '1')}

    @mapping
    def uom_id(self, record):
        
        
        return {'uom_id': 1}
    
    @mapping
    def price(self, record):
        return {'list_price': record.list_price}

    @mapping
    def default_code(self, record):
        code = record['default_code']
        if not code:
            return {'default_code': '/'}
        return {'default_code': code}
        

    @only_create
    @mapping
    def odoo_id(self, record):
        
        match_field = u'default_code' 
#         if self.backend_record.matching_product_product :
#             match_field = self.backend_record.matching_product_ch
#         
#         filters = ast.literal_eval(self.backend_record.local_product_domain_filter)
#         if record[match_field]:
#             filters.append((match_field, '=', record[match_field]))
#            
#         prod_id = self.env['product.product'].search(filters)
#         
#         if len(prod_id) == 1  :            
#             return {'odoo_id': prod_id.id}
        return {}
    
    @mapping
    def category(self, record):
        categ_id= record['categ_id']
        binder = self.binder_for('odoo.product.category')
        #binder.model = 'odoo.product.category'
        cat = binder.wrap_binding(categ_id)
        if not cat:            
            raise MappingError("The product category with "
                                   "odoo id %s is not available." %
                                   mag_category_id)
        return {'categ_id': cat}

