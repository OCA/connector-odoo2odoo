# -*- coding: utf-8 -*-
# © 2015 Malte Jacobi (maljac @ github)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import time
import logging

from openerp.addons.connector.queue.job import job
from openerp.addons.connector.unit.synchronizer import Exporter
from openerp.addons.connector.exception import InvalidDataError

from ..connector import get_environment


_logger = logging.getLogger(__name__)


class OdooExporter(Exporter):

    def __init__(self, connector_env):
        super(OdooExporter, self).__init__(connector_env)
        self.binding_id = None

    def _pre_export_check(self, record):
        """ Check if the record is allowed to be exported."""
        return True

    def _pre_export_domain_check(self, record, domain):
        """ Convinience method to check if a record matches a given domain

        :param record: Odoo record
        :param domain: domain expression, e.g. [('id', '>', '10')]
        """
        # TODO(MJ): Replace this eval expression!
        if record in record.search(eval(domain)):
            return True
        return False

    def _get_remote_model(self):
        """ Use this method to explicitly define a model which shall be called
        in the remote system """
        return

    def _after_export(self, record_created=False):
        """ Hook called at the end of the export

        Use this hook for executing arbitrary actions, e.g. export translations
        :param record_created: indicates whether the record was created
        """
        return

    def run(self, binding_id):
        """ Run the export synchronization

        :param binding_id: identifier for the binding record
        """
        time_start = time.time()
        self.binding_id = binding_id

        record = self.model.browse(binding_id)

        if not self._pre_export_check(record):
            _logger.info('Record did not pass pre-export check.')
            return "Pre-Export check was not successfull"

        mapped_record = self.mapper.map_record(record)

        remote_model = self._get_remote_model()
        external_id = self.binder.to_backend(self.binding_id)
        record_created = False

        # Create a new record or update the existing record
        if external_id:
            _logger.debug('Found binding %s', external_id)
            data = mapped_record.values()
            result = self.backend_adapter.write(
                external_id, data, model_name=remote_model
            )
            if not result:
                # Note: When using @on_record_create / _write events, raising
                #       an exception can lead to inconsistent data.
                #       Example: create product supplierinfo for an supplier
                #       thats is not available in the ic backend.
                # raise InvalidDataError("Something went wrong while writing.")
                return 'Could not export'

        else:
            _logger.debug('No binding found, creating a new record')
            data = mapped_record.values(for_create=True)
            external_id = self.backend_adapter.create(
                data, model_name=remote_model
            )

            if not external_id:
                raise InvalidDataError("Something went wrong while creating.")

            record_created = True

        self.binder.bind(external_id, self.binding_id, exported=True)
        self.external_id = external_id
        self.session.commit()
        self._after_export(record_created=record_created)

        time_end = time.time()
        _logger.warning("Finished exporting record (%s, %s)[%s]",
                        binding_id, external_id, time_end - time_start)


class TranslationExporter(Exporter):
    """ Exporter for translation enabled fields """

    def _get_record(self, language):
        """Get the to be exported recorded in the defined language """
        context = {'lang': language}
        return self.model.with_context(**context).browse(self.binding_id)

    def _get_languages(self):
        """ Hook method for languages to export

        :returns: language codes
        :rtype: list
        """
        term = [('translatable', '=', True)]
        langs = self.env['res.lang'].search(term)
        return [l.code for l in langs]

    def _get_translatable_fields(self):
        """ Get the names of the fields that can be translated

        :returns: list of translatable fields
        :rtype: list
        """
        model_fields = self.model.fields_get()
        trans_fields = [field for field, attrs in model_fields.iteritems()
                        if attrs.get('translate')]
        _logger.debug('Translatable fields: %s', trans_fields)
        return trans_fields

    def run(self, external_id, binding_id, mapper_class=None):
        _logger.debug('Running translation exporter...')
        self.external_id = external_id
        self.binding_id = binding_id

        if mapper_class:
            mapper = self.unit_for(mapper_class)
        else:
            mapper = self.mapper

        trans_fields = self._get_translatable_fields()
        binding = self.model.browse(binding_id)

        if not binding:
            _logger.debug('No binding found for %s, skip translation import',
                          binding_id)
            return

        for language in self._get_languages():
            _logger.debug('Process language %s', language)
            record = self._get_record(language)
            mapped_record = mapper.map_record(record)
            record_values = mapped_record.values()

            # TODO(MJ): As long as we use explicit translation mapper per
            #           model, this logic is actually not necessary.
            #           If we move to a more generic translation mapper, we
            #           might use this logic!
            data = {field: value for field, value in record_values.iteritems()
                    if field in trans_fields}

            _logger.debug('Record values: %s', record_values)
            self.backend_adapter.write(
                external_id, data, context={'lang': language}
            )


@job(default_channel='root.odooconnector')
def export_record(session, model_name, backend_id, binding_id,
                  fields=None, api=None):
    _logger.debug('Export record for "%s"', model_name)
    env = get_environment(session, model_name, backend_id, api=api)

    # TODO: LANGUAGE STUFF
    exporter = env.get_connector_unit(OdooExporter)
    exporter.run(binding_id)
