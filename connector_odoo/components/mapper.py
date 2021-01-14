# -*- coding: utf-8 -*-
# © 2013 Guewen Baconnier,Camptocamp SA,Akretion
# © 2016 Sodexis
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import AbstractComponent
from odoo.addons.connector.components.mapper import mapping, external_to_m2o


def field_by_lang(field):
        ''' ``field`` is the name of the source field.

        Naming the arg: ``field`` is required for the conversion'''
        def modifier(self, record, to_attr):
            ''' self is the current Mapper,
                record is the current record to map,
                to_attr is the target field'''
            lang_code = self.backend_record.get_default_language_code()
            rec_lang = record.with_context(lang=lang_code)
            return rec_lang[field]
        return modifier
    
    
class OdooImportMapper(AbstractComponent):
    _name = 'odoo.import.mapper'
    _inherit = ['base.odoo.connector', 'base.import.mapper']
    _usage = 'import.mapper'
    
    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}


    def _map_direct(self, record, from_attr, to_attr):
        """ Apply the ``direct`` mappings.

        :param record: record to convert from a source to a target
        :param from_attr: name of the source attribute or a callable
        :type from_attr: callable | str
        :param to_attr: name of the target attribute
        :type to_attr: str
        """
        if callable(from_attr):
            return from_attr(self, record, to_attr)

        value = record[from_attr]
        if not value:
            return False

        # Backward compatibility: when a field is a relation, and a modifier is
        # not used, we assume that the relation model is a binding.
        # Use an explicit modifier external_to_m2o in the 'direct' mappings to
        # change that.
        field = self.model._fields[to_attr]
        if field.type == 'many2one':
            mapping_func = external_to_m2o(from_attr)
            value = mapping_func(self, record, to_attr)
        return value


class OdooExportMapper(AbstractComponent):
    _name = 'odoo.export.mapper'
    _inherit = ['base.odoo.connector', 'base.export.mapper']
    _usage = 'export.mapper'

    