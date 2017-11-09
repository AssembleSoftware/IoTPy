.. Model documentation master file, created by
   sphinx-quickstart on Wed Jul 12 09:16:31 2017.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to AssembleSoftware documentation!
==========================================

.. toctree::
   :maxdepth: 2

Core
====
The following modules are all in FINAL/core.

Agent
=====
.. automodule:: agent
.. autoclass:: Agent
   :members: 

Buffer
======
.. automodule:: Buffer
.. autoclass:: Buffer
   :members:

Compute Engine
==============
.. automodule:: compute_engine
.. autoclass:: ComputeEngine
   :members:

Run Agents
==========
.. automodule:: run_agents
.. autoclass:: ComputeEngine
   :members:

Stream
======
.. automodule:: stream
.. autoclass:: Stream
   :members:
.. autoclass:: StreamArray
   :members:
.. autoclass:: _no_value
   :members:
.. autoclass:: _multivalue
   :members:
   
Agent Types
===========
The following modules are all in FINAL/agent_types.

Source
======
.. automodule:: source
.. autofunction:: func_to_q
.. autofunction:: q_to_streams
.. autofunction:: q_to_streams_general
.. autofunction:: source_function
.. autofunction:: source_file
.. autofunction:: source_list

Sink
====
.. automodule:: sink
.. autofunction:: sink_element
.. autofunction:: sink
.. autofunction:: stream_to_list
.. autofunction:: stream_to_file
.. autofunction:: stream_to_queue
.. autofunction:: stream_to_buffer
.. autofunction:: sink_window
.. autofunction:: sink_list
.. autofunction:: sink_list_f

Timed Agent
===========
.. automodule:: timed_agent
.. autofunction:: timed_zip_agent
.. autofunction:: timed_zip
.. autofunction:: timed_window
.. autofunction:: timed_window_function
.. autofunction:: test_timed_zip_agents
.. autofunction:: test_timed_window

Op
==
.. automodule:: op
.. autofunction:: map_element
.. autofunction:: filter_element
.. autofunction:: map_list
.. autofunction:: map_window
.. autofunction:: map_window_list
.. autofunction:: timed_window

Multi
=====
.. automodule:: multi
.. autofunction:: multi_element
.. autofunction:: multi_element_f
.. autofunction:: multi_list
.. autofunction:: multi_list_f
.. autofunction:: multi_window
.. autofunction:: multi_window_f

Merge
=====
.. automodule:: merge
.. autofunction:: zip_map
.. autofunction:: zip_map_f
.. autofunction:: zip_stream
.. autofunction:: zip_stream_f
.. autofunction:: merge_asynch
.. autofunction:: merge_asynch_f
.. autofunction:: mix
.. autofunction:: mix_f
.. autofunction:: blend
.. autofunction:: blend_f
.. autofunction:: merge_window
.. autofunction:: merge_window_f
.. autofunction:: merge_list
.. autofunction:: merge_list_f
.. autofunction:: timed_zip
.. autofunction:: timed_zip_f
.. autofunction:: timed_mix
.. autofunction:: timed_mix_f

Split
=====
.. automodule:: split
.. autofunction:: split_element
.. autofunction:: split_element_f
.. autofunction:: separate
.. autofunction:: separate_f
.. autofunction:: unzip
.. autofunction:: unzip_f
.. autofunction:: timed_unzip
.. autofunction:: timed_unzip_f
.. autofunction:: split_list
.. autofunction:: split_list_f
.. autofunction:: split_window
.. autofunction:: split_window_f

Multiprocessing
===============
The following modules are all in FINAL/multiprocessing.

Component
=========
.. automodule:: Component
.. autofunction:: connect_outputs
.. autofunction:: connect
.. autofunction:: target_of_make_process
.. autofunction:: make_process

Make Process
============
.. automodule:: make_process
.. autoclass:: make_process
   :members: 


.. Remove Indices and tables
    ==================

    * :ref:`genindex`
    * :ref:`modindex`
    * :ref:`search`
