import os

# Resolve the backend/app directory as the package path for imports
_backend_app_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend', 'app'))
__path__ = [_backend_app_path]
