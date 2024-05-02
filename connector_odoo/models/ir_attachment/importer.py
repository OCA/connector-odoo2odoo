import logging

from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping, only_create

_logger = logging.getLogger(__name__)


class IrAttachmentBatchImporter(Component):
    """Import the Odoo Attachment.

    For every Attachment in the list, a delayed job is created.
    Import from a date
    """

    _name = "odoo.ir.attachment.batch.importer"
    _inherit = "odoo.delayed.batch.importer"
    _apply_on = ["odoo.ir.attachment"]

    def run(self, filters=None, force=False):
        """Run the synchronization"""

        external_ids = self.backend_adapter.search(filters)
        _logger.info(
            "search for odoo Attachment %s returned %s items",
            filters,
            len(external_ids),
        )
        for external_id in external_ids:
            job_options = {"priority": 15}
            self._import_record(external_id, job_options=job_options, force=force)


class IrAttachmentImportMapper(Component):
    _name = "odoo.ir.attachment.import.mapper"
    _inherit = "odoo.import.mapper"
    _apply_on = ["odoo.ir.attachment"]

    direct = [
        ("datas", "datas"),
        ("db_datas", "db_datas"),
        ("name", "name"),
        ("description", "description"),
        ("type", "type"),
        ("res_model", "res_model"),
        ("res_name", "res_name"),
        ("store_fname", "store_fname"),
        ("file_size", "file_size"),
        ("index_content", "index_content"),
    ]

    @only_create
    @mapping
    def check_ir_attachment_exists(self, record):
        res = {}

        attachment_id = self.env["ir.attachment"].search(
            [("store_fname", "=", record.store_fname)]
        )
        _logger.info("Attachment found for %s : %s" % (record, attachment_id))
        if len(attachment_id) == 1:
            res.update({"odoo_id": attachment_id.id})
        return res

    @mapping
    def company_id(self, record):
        return {"company_id": self.env.user.company_id.id}

    @mapping
    def res_id(self, record):
        binder = self.binder_for("odoo.{}".format(record.res_model))
        res_id = binder.to_internal(record.res_id, unwrap=True)
        return {"res_id": res_id.id}


class IrAttachmentImporter(Component):
    _name = "odoo.ir.attachment.importer"
    _inherit = "odoo.importer"
    _apply_on = ["odoo.ir.attachment"]

    def _must_skip(
        self,
    ):
        return self.env["ir.attachment"].search(
            [("store_fname", "=", self.odoo_record.store_fname)]
        )
