# project_imports.py
import os
import sys
import importlib.util

def import_module_from_path(module_name, module_path):
    """
    Import a module from a specific path.
    
    Args:
        module_name: The name to give the module
        module_path: The path to the module file
        
    Returns:
        The imported module
    """
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def get_project_root():
    """Return the absolute path to the project root directory."""
    # Adjust this if the file is not at the project root
    return os.path.dirname(os.path.abspath(__file__))
