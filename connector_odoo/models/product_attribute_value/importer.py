# -*- coding: utf-8 -*-
# Copyright 2013-2017 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import logging
from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping, only_create

_logger = logging.getLogger(__name__)


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

class ProductAttributeValueMapper(Component):
    _name = 'odoo.product.attribute.value.mapper'
    _inherit = 'odoo.import.mapper'
    _apply_on = 'odoo.product.attribute.value'

    direct = [('name', 'name'),             
              ('price_extra', 'price_extra'),             
              ]
    
    
    def get_attribute_id(self, record):
        attribute_id = None
        binder = self.binder_for('odoo.product.attribute')
        local_attribute_id = binder.to_internal(record.attribute_id.id, unwrap=True)
        return local_attribute_id.id

    @mapping
    def attribute_id(self, record):
        return {'attribute_id': self.get_attribute_id(record)}
    
    
    @only_create
    @mapping
    def check_att_value_exists(self, record):
        #TODO: Improve and check family, factor etc...
        att_id = self.get_attribute_id(record)
        value_id = self.env['product.attribute.value'].search([
                    ('name', '=', record.name),
                    ('attribute_id', '=', att_id),
                    ])
        res =  {} 
        if len(value_id) == 1  :
            res.update({'odoo_id': value_id.id})             
        return res
        

        