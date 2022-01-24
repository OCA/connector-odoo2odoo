from odoo import fields, models


class OdooResPartnerAddressReferences(models.Model):
    _name = "odoo.res.partner.address.disappeared"
    _inherit = "odoo.binding.disappeared"

    odoo_binding_partner_id = fields.Many2one("odoo.res.partner")
    external_parent_partner_id = fields.Integer()
    partner_id = fields.Many2one(
        "res.partner", string="Partner", required=True, ondelete="cascade"
    )
