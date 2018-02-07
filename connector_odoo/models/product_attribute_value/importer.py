# -*- coding: utf-8 -*-
# Copyright 2013-2017 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import logging
from odoo.addons.component.core import Component

from odoo.addons.connector.components.mapper import mapping, only_create

_logger = logging.getLogger(__name__)

class ProductAttributeValueMapper(Component):
    _name = 'odoo.product.attribute.value.mapper'
    _inherit = 'odoo.import.mapper'
    _apply_on = 'odoo.product.attribute.value'

    direct = [('name', 'name'),             
              ('price_extra', 'price_extra'),             
              ]
    

    @mapping
    def attribute_id(self, record):
        attribute_id = None
        
        binder = self.binder_for('odoo.product.attribute')
        local_attribute_id = binder.to_internal(record.attribute_id.id)
        
        return {'attribute_id': local_attribute_id.id}
    
    
#     @only_create
#     @mapping
#     def check_att_exists(self, record):
#         #TODO: Improve and check family, factor etc...
#         local_uom_id = self.env['product.uom'].search([('name', '=', record.name)])
#         
#         if len(local_uom_id) == 1  :
#             res = local_uom_id.copy_data()[0] #dict((field, value) for field, value in local_uom_id.iteritems())
#             res.update({'odoo_id': local_uom_id.id})
#             
#             return res
#         return {}

class ProductAttributeValueImporter(Component):
    """ Import Odoo Attribute Value """

    _name = 'odoo.product.attribute.value.importer'
    _inherit = 'odoo.importer'
    _apply_on = 'odoo.product.attribute.value'


    def _import_dependencies(self):
        """ Import the dependencies for the record"""
        record = self.odoo_record        
        self._import_dependency(record.attribute_id.id, 'odoo.product.attribute')


#     def _create(self, data):
#         binding = super(ProductUoMImporter, self)._create(data)
#         self.backend_record.add_checkpoint(binding)
#         return binding
    
# class ProductUoM(Component):  
#     _name = 'odoo.product.uom.batch.importer'
#     _inherit = 'odoo.batch.importer'
#     _apply_on = ['odoo.product.uom']
# 
#     def _import_record(self, external_id, job_options=None):
#         """ Delay a job for the import """
#         super(ProductCategoryBatchImporter, self)._import_record(
#             external_id, job_options=job_options
#         )

#     def run(self, filters=None):
        