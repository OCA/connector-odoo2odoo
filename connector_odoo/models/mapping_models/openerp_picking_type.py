from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class OpenERPPickingType(models.Model):
    _name = "openerp.picking.type"

    warehouse_id = fields.Many2one(
        "odoo.stock.warehouse", string="Warehouse", required=True
    )
    type = fields.Char(required=True)
    origin_location_usage = fields.Selection(
        selection=lambda self: self._selection_location_usage()
    )
    dest_location_usage = fields.Selection(
        selection=lambda self: self._selection_location_usage()
    )
    picking_type_id = fields.Many2one(
        "stock.picking.type", string="Picking Type", required=True
    )

    @api.model
    def create(self, vals):
        if not vals.get("origin_location_usage") and not vals.get(
            "dest_location_usage"
        ):
            raise ValidationError(_("Please select at least one location usage"))
        return super().create(vals)

    def write(self, vals):
        for record in self:
            origin_location_usage = vals.get("origin_location_usage")
            if not origin_location_usage and "origin_location_usage" not in vals.keys():
                origin_location_usage = record.origin_location_usage

            dest_location_usage = vals.get("dest_location_usage")
            if not dest_location_usage and "dest_location_usage" not in vals.keys():
                dest_location_usage = record.dest_location_usage

            if not origin_location_usage and not dest_location_usage:
                raise ValidationError(_("Please select at least one location usage"))
            return super().write(vals)

    def _selection_location_usage(self):
        return self.env["stock.location"]._fields["usage"].selection
