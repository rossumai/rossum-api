Request Payloads
================

Some client methods accept the fields of the object being created or updated as keyword
arguments instead of a ``data`` dictionary. The accepted fields are described by the
``TypedDict`` classes below, so type checkers and IDEs can validate and autocomplete them.

.. code-block:: python

   label = client.create_new_label(name="expedite", color="#FF5733")
   label = client.update_part_label(label_id=1, color=None)


Payloads
--------

.. raw:: html

   <h4>Label</h4>

.. autoclass:: rossum_api.payloads.label.LabelWrite
   :no-index-entry:

.. autoclass:: rossum_api.payloads.label.LabelPatch
   :no-index-entry:


See Also
--------

* :doc:`clients` - API clients that accept these payloads
* :doc:`models` - Data models returned by the clients
* `Rossum API Documentation <https://rossum.app/api/docs>`_ - Detailed field descriptions
