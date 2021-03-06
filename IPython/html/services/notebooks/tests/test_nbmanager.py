# coding: utf-8
"""Tests for the notebook manager."""
from __future__ import print_function

import os

from tornado.web import HTTPError
from unittest import TestCase
from tempfile import NamedTemporaryFile

from IPython.utils.tempdir import TemporaryDirectory
from IPython.utils.traitlets import TraitError
from IPython.html.utils import url_path_join

from ..filenbmanager import FileNotebookManager
from ..nbmanager import NotebookManager


class TestFileNotebookManager(TestCase):

    def test_nb_dir(self):
        with TemporaryDirectory() as td:
            fm = FileNotebookManager(notebook_dir=td)
            self.assertEqual(fm.notebook_dir, td)

    def test_missing_nb_dir(self):
        with TemporaryDirectory() as td:
            nbdir = os.path.join(td, 'notebook', 'dir', 'is', 'missing')
            self.assertRaises(TraitError, FileNotebookManager, notebook_dir=nbdir)

    def test_invalid_nb_dir(self):
        with NamedTemporaryFile() as tf:
            self.assertRaises(TraitError, FileNotebookManager, notebook_dir=tf.name)

    def test_get_os_path(self):
        # full filesystem path should be returned with correct operating system
        # separators.
        with TemporaryDirectory() as td:
            nbdir = td
            fm = FileNotebookManager(notebook_dir=nbdir)
            path = fm._get_os_path('test.ipynb', '/path/to/notebook/')
            rel_path_list =  '/path/to/notebook/test.ipynb'.split('/')
            fs_path = os.path.join(fm.notebook_dir, *rel_path_list)
            self.assertEqual(path, fs_path)

            fm = FileNotebookManager(notebook_dir=nbdir)
            path = fm._get_os_path('test.ipynb')
            fs_path = os.path.join(fm.notebook_dir, 'test.ipynb')
            self.assertEqual(path, fs_path)

            fm = FileNotebookManager(notebook_dir=nbdir)
            path = fm._get_os_path('test.ipynb', '////')
            fs_path = os.path.join(fm.notebook_dir, 'test.ipynb')
            self.assertEqual(path, fs_path)

class TestNotebookManager(TestCase):
    
    def make_dir(self, abs_path, rel_path):
        """make subdirectory, rel_path is the relative path
        to that directory from the location where the server started"""
        os_path = os.path.join(abs_path, rel_path)
        try:
            os.makedirs(os_path)
        except OSError:
            print("Directory already exists: %r" % os_path)

    def test_create_notebook(self):
        with TemporaryDirectory() as td:
            # Test in root directory
            nm = FileNotebookManager(notebook_dir=td)
            model = nm.create_notebook()
            assert isinstance(model, dict)
            self.assertIn('name', model)
            self.assertIn('path', model)
            self.assertEqual(model['name'], 'Untitled0.ipynb')
            self.assertEqual(model['path'], '')

            # Test in sub-directory
            sub_dir = '/foo/'
            self.make_dir(nm.notebook_dir, 'foo')
            model = nm.create_notebook(None, sub_dir)
            assert isinstance(model, dict)
            self.assertIn('name', model)
            self.assertIn('path', model)
            self.assertEqual(model['name'], 'Untitled0.ipynb')
            self.assertEqual(model['path'], sub_dir.strip('/'))

    def test_get_notebook(self):
        with TemporaryDirectory() as td:
            # Test in root directory
            # Create a notebook
            nm = FileNotebookManager(notebook_dir=td)
            model = nm.create_notebook()
            name = model['name']
            path = model['path']

            # Check that we 'get' on the notebook we just created
            model2 = nm.get_notebook(name, path)
            assert isinstance(model2, dict)
            self.assertIn('name', model2)
            self.assertIn('path', model2)
            self.assertEqual(model['name'], name)
            self.assertEqual(model['path'], path)

            # Test in sub-directory
            sub_dir = '/foo/'
            self.make_dir(nm.notebook_dir, 'foo')
            model = nm.create_notebook(None, sub_dir)
            model2 = nm.get_notebook(name, sub_dir)
            assert isinstance(model2, dict)
            self.assertIn('name', model2)
            self.assertIn('path', model2)
            self.assertIn('content', model2)
            self.assertEqual(model2['name'], 'Untitled0.ipynb')
            self.assertEqual(model2['path'], sub_dir.strip('/'))
            
    def test_update_notebook(self):
        with TemporaryDirectory() as td:
            # Test in root directory
            # Create a notebook
            nm = FileNotebookManager(notebook_dir=td)
            model = nm.create_notebook()
            name = model['name']
            path = model['path']

            # Change the name in the model for rename
            model['name'] = 'test.ipynb'
            model = nm.update_notebook(model, name, path)
            assert isinstance(model, dict)
            self.assertIn('name', model)
            self.assertIn('path', model)
            self.assertEqual(model['name'], 'test.ipynb')

            # Make sure the old name is gone
            self.assertRaises(HTTPError, nm.get_notebook, name, path)

            # Test in sub-directory
            # Create a directory and notebook in that directory
            sub_dir = '/foo/'
            self.make_dir(nm.notebook_dir, 'foo')
            model = nm.create_notebook(None, sub_dir)
            name = model['name']
            path = model['path']
            
            # Change the name in the model for rename
            model['name'] = 'test_in_sub.ipynb'
            model = nm.update_notebook(model, name, path)
            assert isinstance(model, dict)
            self.assertIn('name', model)
            self.assertIn('path', model)
            self.assertEqual(model['name'], 'test_in_sub.ipynb')
            self.assertEqual(model['path'], sub_dir.strip('/'))
            
            # Make sure the old name is gone
            self.assertRaises(HTTPError, nm.get_notebook, name, path)

    def test_save_notebook(self):
        with TemporaryDirectory() as td:
            # Test in the root directory
            # Create a notebook
            nm = FileNotebookManager(notebook_dir=td)
            model = nm.create_notebook()
            name = model['name']
            path = model['path']

            # Get the model with 'content'
            full_model = nm.get_notebook(name, path)

            # Save the notebook
            model = nm.save_notebook(full_model, name, path)
            assert isinstance(model, dict)
            self.assertIn('name', model)
            self.assertIn('path', model)
            self.assertEqual(model['name'], name)
            self.assertEqual(model['path'], path)

            # Test in sub-directory
            # Create a directory and notebook in that directory
            sub_dir = '/foo/'
            self.make_dir(nm.notebook_dir, 'foo')
            model = nm.create_notebook(None, sub_dir)
            name = model['name']
            path = model['path']
            model = nm.get_notebook(name, path)

            # Change the name in the model for rename
            model = nm.save_notebook(model, name, path)
            assert isinstance(model, dict)
            self.assertIn('name', model)
            self.assertIn('path', model)
            self.assertEqual(model['name'], 'Untitled0.ipynb')
            self.assertEqual(model['path'], sub_dir.strip('/'))

    def test_save_notebook_with_script(self):
        with TemporaryDirectory() as td:
            # Create a notebook
            nm = FileNotebookManager(notebook_dir=td)
            nm.save_script = True
            model = nm.create_notebook()
            name = model['name']
            path = model['path']

            # Get the model with 'content'
            full_model = nm.get_notebook(name, path)

            # Save the notebook
            model = nm.save_notebook(full_model, name, path)

            # Check that the script was created
            py_path = os.path.join(td, os.path.splitext(name)[0]+'.py')
            assert os.path.exists(py_path), py_path

    def test_delete_notebook(self):
        with TemporaryDirectory() as td:
            # Test in the root directory
            # Create a notebook
            nm = FileNotebookManager(notebook_dir=td)
            model = nm.create_notebook()
            name = model['name']
            path = model['path']
            
            # Delete the notebook
            nm.delete_notebook(name, path)
            
            # Check that a 'get' on the deleted notebook raises and error
            self.assertRaises(HTTPError, nm.get_notebook, name, path)
    
    def test_copy_notebook(self):
        with TemporaryDirectory() as td:
            # Test in the root directory
            # Create a notebook
            nm = FileNotebookManager(notebook_dir=td)
            path = u'å b'
            name = u'nb √.ipynb'
            os.mkdir(os.path.join(td, path))
            orig = nm.create_notebook({'name' : name}, path=path)
            
            # copy with unspecified name
            copy = nm.copy_notebook(name, path=path)
            self.assertEqual(copy['name'], orig['name'].replace('.ipynb', '-Copy0.ipynb'))
            
            # copy with specified name
            copy2 = nm.copy_notebook(name, u'copy 2.ipynb', path=path)
            self.assertEqual(copy2['name'], u'copy 2.ipynb')
    
