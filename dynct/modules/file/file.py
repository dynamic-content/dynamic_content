"""
Implementation for file access and page creation. Latter may become dynamic in the future allowing pages to use their
own page handlers.
"""

from pathlib import Path
from urllib.parse import quote_plus
import mimetypes

from dynct.core.mvc.controller import Controller
from dynct.core.mvc.model import Model
from dynct.includes import bootstrap
from dynct.modules.comp.html_elements import ContainerElement, List
from dynct.errors.exceptions import MissingFileError, AccessDisabled


__author__ = 'justusadam'

_template_path = 'themes/default_theme/template/page.html'


class PathHandler(Controller):
    def __init__(self):
        super().__init__(public=self.handle, theme=self.handle)

    def handle(self, model, url, *args):
        self.model = model
        return self.parse_path(url)

    def parse_path(self, url):
        if len(url.path) < 1:
            raise MissingFileError
        basedirs = bootstrap.FILE_DIRECTORIES[url.path[0]]
        if isinstance(basedirs, str):
            basedirs = (basedirs,)
        for basedir in basedirs:
            filepath = '/'.join([basedir] + url.path[1:])
            filepath = Path(filepath)

            if not filepath.exists():
                continue

            filepath = filepath.resolve()
            basedir = Path(basedir).resolve()

            if not bootstrap.ALLOW_HIDDEN_FILES and filepath.name.startswith('.'):
                raise AccessDisabled

            if basedir not in filepath.parents and basedir != filepath:
                raise AccessDisabled
            if filepath.is_dir():
                if not bootstrap.ALLOW_INDEXING:
                    raise AccessDisabled
                elif not url.path.trailing_slash:
                    url.path.trailing_slash = True
                    return Model(':redirect:' + str(url))
                else:
                    return DirectoryHandler(url, filepath).compiled
            else:
                if url.path.trailing_slash:
                    url.path.trailing_slash = False
                    return Model(':redirect:' + str(url))
                self.model['content'] = filepath.open('rb').read()
                self.model.decorator_attributes.add('no-encode')
                self.model.content_type, self.model.encoding = mimetypes.guess_type(str(filepath.name))
                return ':no-view:'

        raise MissingFileError


class DirectoryHandler:
    def __init__(self, url, real_dir):
        self._url = url
        if not isinstance(real_dir, Path):
            Path(real_dir)
        self.directory = real_dir

    view_name = 'page'

    @property
    def url(self):
        return self._url

    def _files(self):
        return filter(lambda a: not str(a.name).startswith('.'), self.directory.iterdir())

    def _render_file_list(self):
        return List(
            *[ContainerElement(
                str(a.name), html_type='a', additional={'href': str(self.url.path) + quote_plus(str(a.name), )},
                classes={'file-link'}
            ) for a in self._files()
            ], classes={'directory-index'}, item_classes={'directory-content'}
        )

    @property
    def compiled(self):
        model = Model('page', title=self.directory.name, content=self._render_file_list())
        model.decorator_attributes.add('no-commons')
        return model
