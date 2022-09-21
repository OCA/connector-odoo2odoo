import logging

from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping

_logger = logging.getLogger(__name__)

_renames = {
    # "product.product,name": "product.template,name",
}


class IrTranslationBatchImporter(Component):
    """Import the Odoo Translation.

    For every Translation in the list, a delayed job is created.
    Import from a date
    """

    _name = "odoo.ir.translation.batch.importer"
    _inherit = "odoo.delayed.batch.importer"
    _apply_on = ["odoo.ir.translation"]

    def run(self, filters=None, force=False):
        """Run the synchronization"""

        external_ids = self.backend_adapter.search(filters)
        _logger.info(
            "search for odoo Translation %s returned %s items",
            filters,
            len(external_ids),
        )
        for external_id in external_ids:
            job_options = {"priority": 15}
            self._import_record(external_id, job_options=job_options, force=force)


class IrTranslationImportMapper(Component):
    _name = "odoo.ir.translation.import.mapper"
    _inherit = "odoo.import.mapper"
    _apply_on = ["odoo.ir.translation"]

    direct = [
        ("lang", "lang"),
        ("src", "src"),
        ("type", "type"),
        ("value", "value"),
    ]

    @mapping
    def odoo_id(self, record):
        binder = self.binder_for("odoo.{}".format(record.name.split(",")[0]))
        res_id = binder.to_internal(record.res_id, unwrap=True)
        name = _renames[record.name] if record.name in _renames.keys() else record.name
        to_translate = name.split(",")
        if record.name in _renames.keys() and to_translate[0] == "product.template":
            res_id = res_id.product_tmpl_id

        translation_id = self.env["ir.translation"].search(
            [
                ("lang", "=", record.lang),
                ("name", "=", name),
                ("type", "=", "model"),
                ("res_id", "=", res_id.id),
            ]
        )
        _logger.info(
            "Translation name %s res_id %s found for %s : %s"
            % (record.name, res_id.id, record.id, translation_id)
        )
        if len(translation_id) == 1:
            return {"odoo_id": translation_id.id}
        return {}

    @mapping
    def res_id(self, record):
        binder = self.binder_for("odoo.{}".format(record.name.split(",")[0]))
        res_id = binder.to_internal(record.res_id, unwrap=True)
        name = _renames[record.name] if record.name in _renames.keys() else record.name
        to_translate = name.split(",")
        if record.name in _renames.keys() and to_translate[0] == "product.template":
            res_id = res_id.product_tmpl_id
        return {"res_id": res_id.id}

    @mapping
    def name(self, record):
        return {
            "name": _renames[record.name]
            if record.name in _renames.keys()
            else record.name
        }


class IrTranslationImporter(Component):
    _name = "odoo.ir.translation.importer"
    _inherit = "odoo.importer"
    _apply_on = ["odoo.ir.translation"]

    def _get_binding_odoo_id_changed(self, binding):
        # In OpenERP, the translation is remove instead of update
        # We need to find the translation to update in Odoo
        if not binding and self.backend_record.version == "6.1":
            binder = self.binder_for(
                "odoo.{}".format(self.odoo_record.name.split(",")[0])
            )
            res_id = binder.to_internal(self.odoo_record.res_id, unwrap=True)
            name = (
                _renames[self.odoo_record.name]
                if self.odoo_record.name in _renames.keys()
                else self.odoo_record.name
            )
            to_translate = name.split(",")
            if (
                self.odoo_record.name in _renames.keys()
                and to_translate[0] == "product.template"
            ):
                res_id = res_id.product_tmpl_id
            translation_id = self.env["ir.translation"].search(
                [
                    ("lang", "=", self.odoo_record.lang),
                    ("name", "=", name),
                    ("type", "=", "model"),
                    ("res_id", "=", res_id.id),
                ]
            )
            binding = self.env["odoo.ir.translation"].search(
                [("odoo_id", "=", translation_id.id)]
            )
        return binding

    def _must_skip(self):
        # If field no exists, we skip the import
        to_translate = self.odoo_record.name.split(",")
        model = to_translate[0]
        field_name = to_translate[1]
        skip = not self.env["ir.model.fields"].search(
            [("model_id.model", "=", model), ("name", "=", field_name)]
        )
        if not skip:
            # If record no exists, we skip the import
            binder = self.binder_for("odoo.{}".format(to_translate[0]))
            res_id = binder.to_internal(self.odoo_record.res_id, unwrap=True)
            skip = not res_id
        return skip

    def _after_import(self, binding, force=False):
        res = super()._after_import(binding, force=force)
        if (
            "product.product," in binding.name
            and not self.backend_record.work_with_variants
        ):
            # Copy product.product translations to transform in product.template translation
            product_product_id = self.env["product.product"].browse(binding.res_id)
            name = "product.template,{}".format(binding.name.split(",")[1])
            ir_translation_id = self.env["ir.translation"].search(
                [
                    ("lang", "=", binding.lang),
                    ("name", "=", name),
                    ("type", "=", "model"),
                    ("res_id", "=", product_product_id.product_tmpl_id.id),
                ]
            )
            if ir_translation_id:
                ir_translation_id.write(
                    {
                        "value": binding.value,
                    }
                )
            else:
                self.env["ir.translation"].with_context(
                    **{"connector_no_export": True}
                ).create(
                    {
                        "comments": binding.odoo_id.comments,
                        "lang": binding.odoo_id.lang,
                        "module": binding.odoo_id.module,
                        "name": name,
                        "res_id": product_product_id.product_tmpl_id.id,
                        "src": binding.odoo_id.src,
                        "state": binding.odoo_id.state,
                        "type": binding.odoo_id.type,
                        "value": binding.odoo_id.value,
                    }
                )
        return res
