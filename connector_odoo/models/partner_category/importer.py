import logging

from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping, only_create

_logger = logging.getLogger(__name__)


class PartnerCategoryBatchImporter(Component):
    """Import the Odoo Partner Category.

    For every partner category in the list, a delayed job is created.
    Import from a date
    """

    _name = "odoo.res.partner.category.batch.importer"
    _inherit = "odoo.delayed.batch.importer"
    _apply_on = ["odoo.res.partner.category"]

    def run(self, filters=None):
        """Run the synchronization"""

        external_ids = self.backend_adapter.search(filters)
        _logger.info(
            "search for odoo partner category %s returned %s items",
            filters,
            len(external_ids),
        )
        for external_id in external_ids:
            job_options = {"priority": 15}
            self._import_record(external_id, job_options=job_options)


class PartnerCategoryImportMapper(Component):
    _name = "odoo.res.partner.category.import.mapper"
    _inherit = "odoo.import.mapper"
    _apply_on = ["odoo.res.partner.category"]

    @only_create
    @mapping
    def check_partner_category_exists(self, record):
        res = {}
        lang = (
            self.backend_record.default_lang_id.code
            or self.env.user.lang
            or self.env.context["lang"]
            or "en_US"
        )
        _logger.debug(
            "CHECK ONLY CREATE PARTNER CATEGORY %s with lang %s"
            % (record["name"], lang)
        )

        local_category_id = (
            self.env["res.partner.category"]
            .with_context(lang=lang)
            .search([("name", "=", record.name)])
        )
        _logger.debug(
            "PARTNER CATEGORY found for %s : %s" % (record, local_category_id)
        )
        if len(local_category_id) == 1:
            res.update({"odoo_id": local_category_id.id})
        return res

    direct = [("name", "name"), ("color", "color")]


class PartnerCategoryImporter(Component):
    _name = "odoo.res.partner.category.importer"
    _inherit = "odoo.importer"
    _apply_on = ["odoo.res.partner.category"]

    def _import_dependencies(self):
        result = super()._import_dependencies()
        return result
