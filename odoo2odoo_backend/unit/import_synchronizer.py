# -*- coding: utf-8 -*-
# Copyright 2016 ABF OSIELL <http://osiell.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging

from openerp import fields, _

from openerp.addons.connector.unit.synchronizer import Importer
from openerp.addons.connector.queue.job import job
from openerp.addons.connector.exception import IDMissingInBackend

from ..connector import get_environment, create_binding

_logger = logging.getLogger(__name__)


class OdooImporter(Importer):
    _model_name = []
    _raw_mode = False

    def run(self, external_ids):
        """Run the synchronization (create or update the local Odoo record)."""
        # Fetch the data on the external Odoo server
        try:
            records_data = self._get_external_data(external_ids)
        except IDMissingInBackend:
            return _("Record(s) does no longer exist "
                     "in the external Odoo server")
        for record_data in records_data:
            external_id = record_data['id']
            self.import_record(external_id, record_data)

    def import_record(self, external_id, record_data):
        """Try to import the external record."""
        binding = self._get_binding(external_id, record_data)
        # Check if the import should be processed
        if not self.check_import(external_id, record_data, binding):
            _logger.info(
                u"%s - Skipping import for the external record (%s,%s)",
                self.backend_record.name, self.model._name, external_id)
            return
        # Keep a lock during the import
        lock_name = 'import({}, {}, {}, {})'.format(
            self.backend_record._name,
            self.backend_record.id,
            self.model._name,
            external_id,
        )
        self.advisory_lock_or_retry(lock_name)
        self._before_import(external_id, record_data, binding)
        # Import the missing record dependencies
        self._import_dependencies(external_id, record_data, binding)
        # Update/create the record
        if binding.external_odoo_id:
            self.update_record(binding, record_data)
        else:
            self.create_record(external_id, record_data)
        self._after_import(binding)
        return True

    def _get_binding(self, external_id, record_data):
        """Try to math a local record with the external one."""
        binding = self.binder.to_openerp(external_id, record_data=record_data)
        return binding

    def check_import(self, external_id, record_data, binding):
        """Check if the external record should be imported."""
        if self._is_uptodate(external_id, record_data, binding):
            return False
        return True

    def update_record(self, binding, record_data):
        mapped_record = self.mapper.map_record(record_data)
        data = mapped_record.values()
        binding = binding.with_context(connector_no_export=True)
        if self._raw_mode:
            record = getattr(binding, self.binder._openerp_field)
            record.o2o_write(data)
        else:
            binding.write(data)
        _logger.info(
            u"%s - Binding record '%s' imported (updated)",
            self.backend_record.name, binding)
        return True

    def create_record(self, external_id, record_data):
        mapped_record = self.mapper.map_record(record_data)
        data = mapped_record.values(for_create=True)
        model = self.model.with_context(connector_no_export=True)
        if self._raw_mode:
            rel_field = self.binder._openerp_field
            model_name = self.model.fields_get(
                [rel_field])[rel_field]['relation']
            model = self.env[model_name]
            record = model.o2o_create(data)
            binding = create_binding(
                self.session, model._name, record.id,
                self.backend_record.id, force=True)
        else:
            data['backend_id'] = self.backend_record.id
            binding = model.create(data)
        self.binder.bind(external_id, binding.id)
        _logger.info(
            u"%s - Binding record '%s' imported (created)",
            self.backend_record.name, binding)
        return binding

    def _get_external_data(self, external_ids):
        """Return the record data from the external Odoo server."""
        return self.backend_adapter.read(external_ids, load='_classic_write')

    def _is_uptodate(self, external_id, record_data, binding):
        """Return True if the local record is already up-to-date."""
        if not record_data.get('write_date'):
            return False
        if not binding:
            return False
        if not binding.sync_date:
            return
        sync_date = fields.Datetime.from_string(binding.sync_date)
        backend_date = fields.Datetime.from_string(record_data['write_date'])
        uptodate = backend_date < sync_date
        if uptodate:
            _logger.info(
                u"%s - External record (%s,%s) is up-to-date",
                self.backend_record.name, self.model._name, external_id)
        return uptodate

    def _before_import(self, external_id, record_data, binding):
        """Hook called before the import, when we have the
        external record data.
        """
        return

    def _after_import(self, binding):
        """Hook called at the end of the import."""
        return

    def _import_dependency(
            self, external_id, binding_model,
            importer_class=None, always=False):
        """ Import a dependency.

        The importer class is a class or subclass of
        :class:`OdooImporter`. A specific class can be defined.

        :param external_id: id of the related binding to import
        :param binding_model: name of the binding model for the relation
        :type binding_model: str | unicode
        :param importer_class: :class:`openerp.addons.connector.\
                                       connector.ConnectorUnit`
                               class or parent class to use for the export.
                               By default: OdooImporter
        :type importer_class: :class:`openerp.addons.connector.\
                                      connector.MetaConnectorUnit`
        :param always: if True, the record is updated even if it already
                       exists, note that it is still skipped if it has
                       not been modified on the external Odoo since the last
                       update. When False, it will import it only when
                       it does not yet exist.
        :type always: boolean
        """
        if not external_id:
            return
        if importer_class is None:
            importer_class = OdooImporter
        binder = self.binder_for(binding_model)
        if always or not binder.to_openerp(external_id):
            importer = self.unit_for(importer_class, model=binding_model)
            importer.run([external_id])

    def _import_dependencies(self, external_id, record_data, binding):
        """Import the dependencies for the record."""
        pass


class BatchOdooImporter(Importer):
    """The role of a BatchOdooImporter is to search for a list of
    items to import, then it can either import them directly or delay
    the import of each item separately.
    """

    def run(self, domain=None, bulk=False):
        """ Run the synchronization """
        if domain is None:
            domain = []
        external_ids = self.backend_adapter.search(domain)
        if bulk:
            self._import_records(external_ids)
            return
        for external_id in external_ids:
            self._import_records([external_id])

    def _import_records(self, external_ids):
        """Import records directly or delay the import of the records.

        Method to implement in sub-classes.
        """
        raise NotImplementedError


class DirectBatchOdooImporter(BatchOdooImporter):
    """Import the records directly, without delaying the jobs."""
    _model_name = None

    def _import_records(self, external_ids):
        """Import the records directly."""
        import_records(
            self.session, self.model._name,
            self.backend_record.id, external_ids)


class DelayedBatchOdooImporter(BatchOdooImporter):
    """Delay import of the records."""
    _model_name = None

    def _import_records(self, external_ids):
        """Delay the import of the records."""
        import_records.delay(
            self.session, self.model._name,
            self.backend_record.id, external_ids)


@job(default_channel='root.o2o')
def import_batch(session, model_name, backend_id, domain=None):
    """Prepare a batch import of records from an external Odoo server."""
    env = get_environment(session, model_name, backend_id)
    importer = env.get_connector_unit(BatchOdooImporter)
    importer.run(domain=domain)


@job(default_channel='root.o2o')
def import_records(session, model_name, backend_id, external_ids):
    """Import records from an external Odoo server."""
    env = get_environment(session, model_name, backend_id)
    importer = env.get_connector_unit(OdooImporter)
    _logger.info(
        u"%s - Importing external record '(%s,%s)'...",
        env.backend_record.name, model_name, external_ids)
    importer.run(external_ids)
