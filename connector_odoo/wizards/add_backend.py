# -*- coding: utf-8 -*-
# Copyright <YEAR(S)> <AUTHOR(S)>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models, fields


class WizardModel(models.TransientModel):
    _name = "connector_odoo.add_backend.wizard"

    @api.multi
    def get_default_products(self):
        
        domain = []
        active_ids = self.env.context.get('active_ids', False)
        active_model = self.env.context.get('active_model', False)
        
        if not active_model == 'product.product':
            raise
        
        if active_ids and active_model == 'product.template' :
           domain.append(('id', 'in', active_ids))
            
        products = self.env['product.product'].search(domain)
        return products
        
    @api.multi 
    def check_backend_binding(self):
        
        prod_ids = [p.id for p in self.product_ids]
        
        
        odoo_prod_ids = self.env['odoo.product.product'].search(
                                    [('odoo_id', 'in', prod_ids),
                                    ('backend_id', '=', self.backend_id.id)])
        prod_already_bind = [p.odoo_id.id for p in odoo_prod_ids]
        prod_already_bind_ids = self.env['product.product'].search(
                                        [('id', 'in', prod_already_bind)])
        
        prod_to_export = self.product_ids - prod_already_bind_ids
        
        for prod in prod_to_export:
            vals = {'odoo_id': prod.id,
                    'external_id': 0,
                    'backend_id': self.backend_id.id                
                }
            
            self.env['odoo.product.product'].create(vals)

    backend_id = fields.Many2one(comodel_name='odoo.backend', required=True)
    product_ids = fields.Many2many(comodel_name='product.product', default=get_default_products)
    
    
    @api.multi
    def action_accept(self):
        self.ensure_one()
        self.check_backend_binding()
