from notebook.notebookapp import NotebookApp
from traitlets import Unicode

from .config import NteractConfig

class NteractApp(NotebookApp):
    """Application for runing nteract on a jupyter notebook server."""

    default_url = Unicode('/nteract/edit/app_notebook.ipynb', help="nteract's default starting location")

    classes = [*NotebookApp.classes, NteractConfig]


main = launch_new_instance = NteractApp.launch_instance

if __name__ == '__main__':
    main()
