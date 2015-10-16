# -*- coding: utf-8 -*-
# © 2015 Malte Jacobi (maljac @ github)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import logging
import time

from openerp import fields, _
from openerp.addons.connector.queue.job import job
from openerp.addons.connector.unit.synchronizer import Importer

from ..connector import get_environment


_logger = logging.getLogger(__name__)


class OdooImporter(Importer):

    _ic_model_name = None

    def __init__(self, connector_env):
        """
        :param connector_env: current environment (backend, session, ...)
        """
        super(OdooImporter, self).__init__(connector_env)

        # We define helper attributes thus we do not have to define
        # the parameters in each method call
        self.external_id = None
        self.external_record = None

    def _get_external_data(self, fields=None):
        """ Return the raw data """
        return self.backend_adapter.read(self.external_id,
                                         fields=fields,
                                         model_name=self._ic_model_name)

    def _is_uptodate(self, binding):
        """ Check if the import is uptodate and should be skipped.

        :returns: True if the import is uptodate
        """
        assert self.external_record

        # no write date --> import it
        if not self.external_record.get('write_date'):
            return False

        # no binding exist, so the record does not exist --> import it
        if not binding:
            return False

        # the binding has no sync_date --> import it
        if not binding.sync_date:
            return False

        # compare external date and binding sync date
        date_from_string = fields.Datetime.from_string
        sync_date = date_from_string(binding.sync_date)
        external_date = date_from_string(
            self.external_record['write_date'])

        return external_date < sync_date

    def _get_binding(self):
        """ Return the binding for the external ID """
        return self.binder.to_openerp(self.external_id, browse=True)

    def _map_data(self):
        """ Return the mapped record based on the external_record """
        return self.mapper.map_record(self.external_record)

    def _create_data(self, map_record, **kwargs):
        """ Return the mapped values for creation """
        return map_record.values(for_create=True, **kwargs)

    def _update_data(self, map_record, **kwargs):
        """ Return the mapped values for updates """
        return map_record.values(**kwargs)

    def _create(self, data):
        """ Create the Odoo record

        :returns: create Odoo record ID
        """
        model = self.model.with_context(connector_no_export=True)
        binding = model.create(data)
        _logger.debug('Created a new Odoo record with data: {}'.format(data))
        return binding

    def _update(self, binding, data):
        """ Update an existing Odoo record

        :param binding: model binding recordset
        :param data: dictionary of data to update
        :returns: None
        """
        binding.with_context(connector_no_export=True).write(data)
        _logger.debug('Updated a Odoo record')
        return

    def _after_import(self, binding):
        """ Hook called at the end of the import

        Use this to import related stuff like translations.
        """
        return

    def run(self, external_id, force=False):
        """ Run the synchronization

        :param external_id: identifier of the record in the remote system
        :param force: force import even if the record is already up-to-date
        """
        time_start = time.time()
        self.external_id = external_id

        # Get data from external backend
        self.external_record = self._get_external_data(
            fields=['write_date'])

        # Try to get a binding
        binding = self._get_binding()
        _logger.debug("Found binding: %s", binding)

        if not force and self._is_uptodate(binding):
            time_end = time.time()
            _logger.info('Skip the import record is up-to-date (%s, %s) [%s]',
                         binding.openerp_id, binding.external_id,
                         time_end - time_start)
            return _('Already up-to-date, skipt the import.')

        self.external_record = self._get_external_data()
        # Map the data
        mapped_record = self._map_data()

        # Create a new or update the existing record
        if binding:
            record = self._update_data(mapped_record)
            self._update(binding, record)
        else:
            record = self._create_data(mapped_record)
            binding = self._create(record)
        # Finally bind the record with the external_id
        self.binder.bind(self.external_id, binding)

        self._after_import(binding)

        time_end = time.time()
        _logger.warning("Finished importing record (%s, %s) [%s]",
                        binding.openerp_id, binding.external_id,
                        time_end - time_start)


class TranslationImporter(Importer):
    """ Importer for translation enabled fields """

    _ic_model_name = None

    def _get_languages(self):
        """ Hook method for languages to retrieve

        :returns: list of language codes
        """
        term = [('translatable', '=', True)]
        langs = self.env['res.lang'].search(term)
        return [l.code for l in langs]

    def _get_external_data(self, language):
        """ Return the raw data """
        context = {'lang': language}
        return self.backend_adapter.read(self.external_id,
                                         context=context,
                                         model_name=self._ic_model_name)

    def run(self, external_id, binding_id, mapper_class=None):
        """ Run the translations import

        :param external_id: identifier of the record in the remote system
        :param binding_id: id of the binding in openerp
        :param mapper_class: Use a specific mapper class.
                             E.g. if no children or other special fields are
                             needed you should use a more simpler mapper class
        """
        _logger.debug('Running translation importer...')
        # Setting IDs for convinience
        self.external_id = external_id
        self.binding_id = binding_id

        # Choose which mapper class to use
        if mapper_class:
            mapper = self.unit_for(mapper_class)
        else:
            mapper = self.mapper

        # Find translatable fields
        model_fields = self.model.fields_get()
        trans_fields = [field for field, attrs in model_fields.iteritems()
                        if attrs.get('translate')]

        binding = self.model.browse(binding_id)

        for language in self._get_languages():
            _logger.debug('Process language %s', language)
            external_record = self._get_external_data(language)
            mapped_record = mapper.map_record(external_record)
            record = mapped_record.values()

            data = {field: value for field, value in record.iteritems()
                    if field in trans_fields}

            _logger.debug('For translation update the following fields %s',
                          data)

            binding.with_context(connector_no_export=True,
                                 lang=language).write(data)


class BatchImporter(Importer):
    """ Search for a list of items to import. Import them directly or delay
    the import of each item (see DirectBatchImporter, DelayedBatchImporter)
    """
    _ic_model_name = None

    def run(self, filters=None):
        """ Run the synchronization """
        _logger.debug("BatchImporter started")
        record_ids = self.backend_adapter.search(
            filters, model_name=self._ic_model_name)

        for record_id in record_ids:
            self._import_record(record_id, api=self.connector_env.api)

    def _import_record(self, record_id, api=None):
        """ Import the record directly or delay it.

        Method must be implemented in sub-classes.
        """
        raise NotImplementedError


class DirectBatchImporter(BatchImporter):
    """ Import the records directly. Do not delay import to jobs. """

    _model_name = None
    _ic_model_name = None

    def _import_record(self, record_id, api=None):
        """ Import record directly """
        import_record(self.session, self.model._name, self.backend_record.id,
                      record_id, api=api)


@job
def import_batch(session, model_name, backend_id, filters=None):
    """ Prepare a batch import of records """
    _logger.debug("Import batch for '{}'".format(model_name))
    env = get_environment(session, model_name, backend_id)
    importer = env.get_connector_unit(BatchImporter)
    importer.run(filters=filters)


@job
def import_record(session, model_name, backend_id, external_id, api=None):
    """ Import a record """
    _logger.debug("Import record for '{}'".format(model_name))

    env = get_environment(session, model_name, backend_id, api=api)

    lang = env.backend_record.default_lang_id
    lang_code = lang.code if lang else 'en_US'

    # FIXME: Logic for context change must be in `get_environment`
    with env.session.change_context(lang=lang_code):
        importer = env.get_connector_unit(OdooImporter)
        importer.run(external_id)
