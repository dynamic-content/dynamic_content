import functools

from dynct import core
from dynct.core.mvc import decorator as mvc_dec
from dynct.modules.comp import decorator as comp_dec
from dynct.modules.comp import html
from dynct.util import lazy
from dynct.core import model as coremodel
from dynct.modules.commons import menus as _menus
from dynct.modules.users import decorator as user_dec
from . import model as _model, node as _nodemodule, field


__author__ = 'justusadam'

_access_modifier = 'access'
_edit_modifier = 'edit'
_add_modifier = 'add'

_publishing_flag = 'published'

_step = 5

_scroll_left = '<'
_scroll_right = '>'


def not_over(a, val):
    if a > val:
        return val
    else:
        return a


def not_under(a, val=0):
    if a < val:
        return val
    else:
        return a


@core.Component('IrisCompilers')
class Compilers(lazy.Loadable):
    def __init__(self):
        self._dict = None
        super().__init__()

    @lazy.ensure_loaded
    def __getitem__(self, item):
        if isinstance(item, coremodel.ContentTypes):
            item = item.machine_name
        return self._dict[item]

    def load(self):
        self._dict = {ct.machine_name: FieldBasedPageContent(ct) for ct in coremodel.ContentTypes.select()}


class FieldBasedPageContent(object):
    _editorial_list_base = edits = [('edit', _edit_modifier)]
    _view_name = 'page'
    page_type = 'iris'

    def __init__(self, content_type):
        self.dbobj = content_type
        self.content_type = content_type.machine_name
        self.fields = self.get_fields()
        self.modules = core.Modules
        self.theme = self.dbobj.theme

    def get_permission(self, page, modifier):
        return self.join_permission(modifier) if page.published else \
            self.join_permission('access unpublished')

    def compile(self, model, page, modifier, pre_compile_hook=None, post_compile_hook=None, content_compiler_hook=None):

        model.client.check_permission(self.get_permission(page, modifier))

        pre_compile_hook() if pre_compile_hook else None

        node = _nodemodule.Node(
            editorial=self.editorial(page, model.client),
            content=content_compiler_hook(page) if content_compiler_hook else ''.join(
                str(a) for a in self.field_contents(page)),
            title=page.page_title)

        post_compile_hook() if post_compile_hook else None

        return node

    def field_contents(self, page):
        f = lambda a: a['content']
        for single_field in self.fields:
            yield f(single_field.access(page))

    def field_edit(self, page):
        f = lambda a: (html.Label(a.name, label_for=a.name), a['content'])
        for single_field in self.fields:
            for s in f(single_field.edit(page)):
                yield s

    def access(self, model, page):
        return self.compile(model, page, 'access')

    def edit(self, model, page):
        return self.compile(model, page, 'edit', content_compiler_hook=functools.partial(self.edit_form, self))

    def process_edit(self, model, page, post):
        model.client.check_permission(self.get_permission(page, 'add'))
        print(post)
        success = True
        return ':redirect:/iris/' + str(page.oid) + ('' if success else '/add')

    def add(self):
        pass

    def edit_form(self, page):
        content = [self.title_options(page)]
        content += ''.join(self.field_edit(page))
        table = html.TableElement(*content, classes={'edit', page.content_type, 'edit-form'})
        return html.FormElement(table, self.admin_options(page), action='/iris/' + str(page.oid) + '/edit')

    def editorial(self, page, client):
        l = self.editorial_list(page, client)
        if l:
            return html.List(
                *[html.ContainerElement(name, html_type='a', classes={'editorial-link'}, additional={'href': link}) for
                  name, link in l],
                classes={'editorial-list'}
            )
        else:
            return ''

    def join_permission(self, modifier):
        return ' '.join([modifier, 'content type', self.content_type])

    def get_fields(self):
        field_info = _model.FieldConfig.select().where(_model.FieldConfig.content_type == self.dbobj)
        for a in field_info:
            yield field.Field(a, self.page_type)

    def editorial_list(self, page, client):
        for (name, modifier) in self._editorial_list_base:
            if client.check_permission(self.join_permission(modifier)):
                yield (name, '/'.join(['', self.page_type, str(page.oid), modifier]))

    @staticmethod
    def admin_options(page):
        if page.menu_item:
            parent = '-1' if page.menu_item.parent_item is None else page.menu_item.parent_item
            selected = '-'.join([page.menu_item.menu, str(parent)])
            m_c = _menus.menu_chooser('parent-menu', selected=selected)
        else:
            m_c = _menus.menu_chooser('parent-menu')
        menu_options = html.TableRow(
            html.Label('Menu Parent', label_for='parent-menu'), m_c, classes={'menu-parent'})
        publishing_options = html.TableRow(
            html.Label('Published', label_for='toggle-published'),
            html.Checkbox(element_id='toggle-published', value=_publishing_flag, name=_publishing_flag,
                          checked=page.published), classes={'toggle-published'})

        return html.TableElement(publishing_options, menu_options, classes={'admin-options'})

    @staticmethod
    def title_options(page):
        return [html.Label('Title', label_for='edit-title'),
                html.TextInput(element_id='edit-title', name='title', value=page.page_title, required=True, size=100)]


@mvc_dec.controller_function('iris', '/([0-9]+)/?(access)?', get=False, post=False)
@comp_dec.Regions
@_nodemodule.node_process
def handle_compile(model, page_id, modifier):
    page = _model.Page.get(oid=page_id)
    modifiers = {

    }
    return getattr(core.get_component('IrisCompilers')[page.content_type],
                   modifiers.get(modifier, modifier) if modifier else 'access')(model, page)


@mvc_dec.controller_function('iris', '/([0-9]+)/edit', get=False, post=True)
def handle_edit(model, page_id, post):
    page = _model.Page.get(oid=page_id)
    return core.get_component('IrisCompilers')[page.content_type.machine_name].process_edit(model, page_id, post)


@mvc_dec.controller_function('iris', '$', post=False)
@user_dec.authorize(' '.join(['access', 'iris', 'overview']))
@comp_dec.Regions
@_nodemodule.node_process
def overview(page_model, get):
    compiler_map = core.get_component('IrisCompilers')
    my_range = [
        int(get['from'][0]) if 'from' in get else 0,
        int(get['to'][0]) if 'to' in get else _step
    ]
    for a in _model.Page.select().limit(
            ','.join([str(a) for a in [my_range[0], my_range[1] - my_range[0] + 1]])).order_by('date_created desc'):
        node = compiler_map[a.content_type.machine_name].access(page_model, a.oid)
        node['title'] = html.A('/iris/' + str(a.oid), node['title'])
        yield node
