from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class OdooBindingDisappeared(models.AbstractModel):
    """Abstract Model for the Bindings of disappeared models in current Odoo version.

    All the disappeared models used as bindings between OpenERP and Odoo
    (``odoo.res.partner.address.disappeared``, ...) should
    ``_inherit`` it.
    """

    _name = "odoo.binding.disappeared"
    _inherit = "external.binding"
    _description = "Odoo Disappeared Binding (abstract)"

    backend_id = fields.Many2one(
        comodel_name="odoo.backend",
        string="Odoo Backend",
        required=True,
        ondelete="restrict",
    )
    external_id = fields.Integer(string="ID on Ext Odoo", default=-1)

    @api.constrains("backend_id", "external_id")
    def unique_backend_external_id(self):
        if self.external_id > 0:
            count = self.env[self._name].search_count(
                [
                    ("backend_id", "=", self.backend_id.id),
                    ("external_id", "=", self.external_id),
                    ("id", "!=", self.id),
                ]
            )
            if count > 0:
                raise ValidationError(
                    _(
                        "A binding already exists with the same backend '%(backend)s' "
                        "for the external id %(external_id)s of the model %(name)s"
                    )
                    % (self.backend_id.name, self.external_id, self._name)
                )
