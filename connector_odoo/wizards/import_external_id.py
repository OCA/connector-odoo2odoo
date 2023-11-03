# Copyright 2022 GreenIce, Fernando La Chica
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ImportExternalIdModel(models.TransientModel):
    _name = "import.external.id.wizard"

    def _get_default_backend(self):
        return self.env["odoo.backend"].search([], limit=1).id

    backend_id = fields.Many2one(
        "odoo.backend", required=True, default=_get_default_backend
    )
    model_id = fields.Many2one(
        "ir.model", required=True, domain="[('model', 'like', 'odoo.%')]"
    )
    external_id = fields.Integer(required=True)
    force = fields.Boolean(default=True)

    def import_external_id(self):
        self.ensure_one()
        self.backend_id.import_external_id(
            self.model_id.model, self.external_id, self.force
        )
