# -*- coding: utf-8 -*-
# © 2016 ABF OSIELL <http://osiell.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models

from openerp.addons.connector.unit.mapper import (
    mapping, ImportMapper, ExportMapper)

from .export_synchronizer import OdooExporter

COLUMNS_BLACKLIST = models.MAGIC_COLUMNS[:]
COLUMNS_BLACKLIST += ['__last_update']


class OdooImportMapper(ImportMapper):
    _model_name = None

    @mapping
    def odoo2odoo(self, data):
        """Transform an external Odoo's record to its local Odoo's counterpart.
        This method has to return a dictionary of values, e.g.
        for a `product.product` record::

            return {
                'name': u"Test",
                'default_code': u"Test",
            }

        By default the method will map all basic field values present in
        `data` (as long as they exist in the targeted data model) and Many2one
        fields which are involved in the synchronization mechanism.
        """
        model2binding = self.backend_record.get_model_bindings()
        fields_data = self.model.fields_get([])
        # Clean up data
        local_fields = set(
            k for k, v in fields_data.iteritems()
            if not v['type'].endswith('2many'))
        remote_fields = set(data)
        import_fields = list(
            local_fields.intersection(remote_fields) - set(COLUMNS_BLACKLIST))
        for field in list(data):
            if field not in import_fields:
                data.pop(field)
        # Map linked record
        for field in data.keys():
            if not data[field]:
                continue
            # Map the value of Many2one/Reference fields
            if fields_data[field]['type'] in ('many2one', 'reference'):
                relation = ''
                # Many2one
                if fields_data[field]['type'] == 'many2one':
                    relation = fields_data[field]['relation']
                # Reference
                elif fields_data[field]['type'] == 'reference':
                    relation = data[field].split(',')[0]
                # Skip if the targeted relation is not involved
                if not relation or relation not in model2binding:
                    data.pop(field)
                    continue
                # Get the relevant binding
                binding_model = model2binding[relation]
                binder = self.binder_for(binding_model)
                binding = binder.to_openerp(data[field])
                data[field] = binding.odoo_id.id
        return data


class OdooExportMapper(ExportMapper):
    _model_name = None

    @mapping
    def odoo2odoo(self, binding):
        """Transform a Odoo's record to its external Odoo's counterpart.
        This method has to return a dictionary of values as expected
        by the external Odoo.

        By default the method generates a dictionary with all basic
        field values of the record (char, float, boolean...) and Many2one
        fields which are involved in the synchronization mechanism (the
        `get_model_bindings()` method of the 'odoo.backend' data model should
        be overridden to list all data models involved in the synchronization).
        """
        model2binding = self.backend_record.get_model_bindings()
        # In raw mode we limit the fields to be exported (only those owned by
        # the data model exported)
        exporter = self.unit_for(OdooExporter, self.model._name)
        field_names = []
        if exporter._raw_mode:
            field_names = list(binding.odoo_id._columns)
        fields_data = binding.odoo_id.fields_get(field_names)
        fields_to_read = []
        for field, fdata in fields_data.iteritems():
            if field in COLUMNS_BLACKLIST:
                continue
            if fdata['type'] in ['many2many', 'one2many']:
                continue
            if fdata['type'] in ['many2one'] \
                    and fdata['relation'] not in model2binding:
                continue
            fields_to_read.append(field)
        data = binding.odoo_id.o2o_read(
            fields_to_read, load='_classic_write')[0]
        for field, value in data.iteritems():
            if not value:
                continue
            fdata = fields_data[field]
            # Map the value of Many2one/Reference fields
            if fdata['type'] in ('many2one', 'reference'):
                relation = ''
                # Many2one
                if fields_data[field]['type'] == 'many2one':
                    relation = fields_data[field]['relation']
                # Reference
                elif fields_data[field]['type'] == 'reference':
                    relation = value.split(',')[0]
                # Skip if the targeted relation is not involved
                if not relation or relation not in model2binding:
                    data.pop(field)
                    continue
                # Get the relevant binding
                binding_model = model2binding[relation]
                binding = self.env[binding_model].search(
                    [('backend_id', '=', self.backend_record.id),
                     ('odoo_id', '=', value)])
                data[field] = binding.external_odoo_id
        return data
