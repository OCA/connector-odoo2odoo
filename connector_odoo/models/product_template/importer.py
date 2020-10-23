# -*- coding: utf-8 -*-
# Copyright 2013-2017 Camptocamp SA
# © 2016 Sodexis
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import logging
import urllib2
import base64
import sys
import ast

from odoo import _
from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping, only_create
from odoo.addons.connector.exception import MappingError, InvalidDataError
# from ...components.mapper import normalize_datetime

_logger = logging.getLogger(__name__)


class ProductTemplateBatchImporter(Component):
    """ Import the Odoo Products Template.

    For every product category in the list, a delayed job is created.
    Import from a date
    """
    _name = 'odoo.product.template.batch.importer'
    _inherit = 'odoo.delayed.batch.importer'
    _apply_on = ['odoo.product.template']

    def run(self, filters=None):
        """ Run the synchronization """
    
        external_ids = self.backend_adapter.search(filters,)
        _logger.info('search for odoo products template %s returned %s',
                     filters, external_ids)
        for external_id in external_ids:
            #TODO : get the parent_left of the category so that we change the priority
            prod_id = self.backend_adapter.read(external_id)
            cat_id =  self.backend_adapter.read(prod_id.categ_id.id, model='product.category')
            
            job_options = {
                        'priority': 15 + cat_id.parent_left or 0,
                    }
            
            self._import_record(external_id, job_options=job_options)


class ProductTemplateImportMapper(Component):
    _name = 'odoo.product.template.import.mapper'
    _inherit = 'odoo.import.mapper'
    _apply_on = ['odoo.product.template']

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
        if self.backend_record.matching_product_product :
            match_field = self.backend_record.matching_product_ch
        
        filters = ast.literal_eval(self.backend_record.local_product_domain_filter)
        if record[match_field]:
            filters.append((match_field, '=', record[match_field]))
                
        prod_id = self.env['product.product'].search(filters)
        
        if len(prod_id) == 1  :            
            return {'odoo_id': prod_id.id}
        return {}
    
    @mapping
    def category(self, record):
        categ_id= record['categ_id']
        binder = self.binder_for('odoo.product.category')
 
        cat = binder.to_internal(categ_id.id, unwrap=True)
        if not cat:
                raise MappingError("The product category with "
                                   "odoo id %s is not imported." %
                                   mag_category_id)
        return {'categ_id': cat.id}
    
class ProductTemplateImporter(Component):
    _name = 'odoo.product.template.importer'
    _inherit = 'odoo.importer'
    _apply_on = ['odoo.product.template']

    def _import_dependencies(self):
        """ Import the dependencies for the record"""
        record = self.odoo_record
        # import related categories
        categ_id = self.odoo_record.categ_id 
        self._import_dependency(categ_id.id,
                                    'odoo.product.category')


    def _must_skip(self):
        """ Hook called right after we read the data from the backend.

        If the method returns a message giving a reason for the
        skipping, the import will be interrupted and the message
        recorded in the job (if the import is called directly by the
        job, not by dependencies).

        If it returns None, the import will continue normally.

        :returns: None | str | unicode
        """


    def _create(self, data):
        binding = super(ProductTemplateImporter, self)._create(data)
        self.backend_record.add_checkpoint(binding)
        return binding

    def _after_import(self, binding):
        """ Hook called at the end of the import """
#         translation_importer = self.component(
#             usage='translation.importer',
#         )
#         translation_importer.run(
#             self.external_id,
#             binding,
#             mapper='odoo.product.product.import.mapper'
#         )
#         image_importer = self.component(usage='product.image.importer')
#         image_importer.run(self.external_id, binding)
# 
#         if self.odoo_record['type_id'] == 'bundle':
#             bundle_importer = self.component(usage='product.bundle.importer')
#             bundle_importer.run(binding, self.odoo_record)

