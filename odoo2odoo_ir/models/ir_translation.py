# -*- coding: utf-8 -*-
# Copyright 2018 ABF OSIELL <http://osiell.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp import api, fields, models

from openerp.addons.connector.event import Event
from openerp.addons.connector.session import ConnectorSession

from openerp.addons.odoo2odoo_backend.connector import create_bindings
from openerp.addons.odoo2odoo_backend.backend import odoo

from ..consumer import OdooSyncExportMapper, OdooSyncExporter


on_translation_update = Event()


class IrTranslation(models.Model):
    _inherit = 'ir.translation'

    odoo_bind_ids = fields.One2many(
        'odoo.ir.translation',
        inverse_name='odoo_id',
        string=u"Odoo Bindings",
        readonly=True)

    @api.model
    def create(self, vals):
        """Overloaded to handle the standard record duplication mechanism.
        The BaseModel.copy_translations(...) method call the 'read(...)' method
        and send directly the result to the 'create(...)' method, without
        cleaning values from One2Many fields resulting in a nasty exception
        (i.e. 'odoo_bind_ids' field here).
        """
        print self.env.context
        if 'odoo_bind_ids' in vals:
            del vals['odoo_bind_ids']
        return super(IrTranslation, self).create(vals)

    def _set_ids(self, cr, uid, name, tt, lang, ids, value, src=None):
        result = super(IrTranslation, self)._set_ids(
            cr, uid, name, tt, lang, ids, value, src)
        if tt == 'model':
            cr.execute("""
                SELECT id FROM ir_translation
                WHERE lang=%s
                AND type=%s
                AND name=%s
                AND res_id IN %s
            """, (lang, tt, name, tuple(ids),))
            translation_ids = [row[0] for row in cr.fetchall()]
            session = ConnectorSession(cr, uid, context={})
            for translation_id in translation_ids:
                vals = {
                    'name': name,
                    'tt': tt,
                    'lang': lang,
                    'ids': ids,
                    'value': value,
                    'src': src,
                }
                on_translation_update.fire(
                    session, self._name, translation_id, vals)
        return result


class OdooIrTranslation(models.Model):
    _name = 'odoo.ir.translation'
    _inherit = 'odoo.binding'
    _inherits = {'ir.translation': 'odoo_id'}

    odoo_id = fields.Many2one(
        'ir.translation',
        string=u"Translation",
        required=True,
        ondelete='cascade')


@odoo(replacing=OdooSyncExportMapper)
class OdooIrTranslationExportMapper(OdooSyncExportMapper):
    _model_name = 'odoo.ir.translation'

    def odoo2odoo(self, binding):
        model2binding = self.backend_record.get_model_bindings()
        model_name = binding.name.split(',')[0]
        binding_model = model2binding[model_name]
        binder = self.binder_for(binding_model)
        external_res_id = binder.to_backend(binding.res_id, wrap=True)
        data = {
            'name': binding.name,
            'res_id': external_res_id,
            'lang': binding.lang,
            'type': binding.type,
            'src': binding.src,
            'value': binding.value,
            'module': binding.module,
            'state': binding.state,
            'comments': binding.comments,
        }
        return data


@odoo(replacing=OdooSyncExporter)
class OdooIrTranslationExporter(OdooSyncExporter):
    _model_name = 'odoo.ir.translation'

    def check_export(self, binding):
        return binding.type == 'model'


@on_translation_update(model_names='ir.translation')
def on_event_create_bindings(session, model_name, record_id, vals):
    create_bindings(session, model_name, record_id)
