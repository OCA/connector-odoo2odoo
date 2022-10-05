from odoo import fields, models


class OdooIrTranslation(models.Model):
    _name = "openerp.picking.type"

    warehouse_id = fields.Many2one("odoo.stock.warehouse", string="Warehouse")
    type = fields.Char()
    picking_type_id = fields.Many2one("stock.picking.type", string="Picking Type")
