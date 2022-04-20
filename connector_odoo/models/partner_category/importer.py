import logging

from odoo.addons.component.core import Component

_logger = logging.getLogger(__name__)


class PartnerCategoryBatchImporter(Component):
    """Import the Odoo Partner Category.

    For every partner category in the list, a delayed job is created.
    Import from a date
    """

    _name = "odoo.res.partner.category.batch.importer"
    _inherit = "odoo.delayed.batch.importer"
    _apply_on = ["odoo.res.partner.category"]


class PartnerCategoryImportMapper(Component):
    _name = "odoo.res.partner.category.import.mapper"
    _inherit = "odoo.import.mapper"
    _apply_on = ["odoo.res.partner.category"]

    direct = [("name", "name"), ("color", "color")]


class PartnerCategoryImporter(Component):
    _name = "odoo.res.partner.category.importer"
    _inherit = "odoo.importer"
    _apply_on = ["odoo.res.partner.category"]
