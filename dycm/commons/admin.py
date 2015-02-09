from dyc import route
from dyc.util import html
from dycm import i18n
from dyc.middleware import csrf
from . import model as _model, menus as _menus, decorator

__author__ = 'Justus Adam'


@route.controller_class
class MenuAdminController:
    @route.controller_method('menus')
    @decorator.Regions
    def handle_menus(self, dc_obj, url):
        if len(url.path) == 1:
            return self.overview(dc_obj, url)
        elif len(url.path) == 2:
            return self.a_menu(dc_obj, url)

    @staticmethod
    def overview(dc_obj, url):
        menus = _model.Menu.select()
        l = [
            [
                html.A(str(url.path) + '/' + item.machine_name, item.id),
                html.A(str(url.path) + '/' + item.machine_name, i18n.translate(item.display_name)),
                html.Checkbox(checked=bool(item.enabled))
            ] for item in menus]
        dc_obj.context['content'] = csrf.SecureForm(html.TableElement(*l, classes={'menu-overview'}))
        dc_obj.context['title'] = 'Menus Overview'
        dc_obj.config['theme'] = 'admin_theme'
        return 'page'

    @staticmethod
    def a_menu(dc_obj, url):
        menu_name = url.path[1]
        menu = _menus.menu(menu_name).render()
        dc_obj.context['content'] = html.List(*menu, additional={'style': 'list-style-type: none;'})
        dc_obj.context['title'] = i18n.translate(menu_name)
        dc_obj.config['theme'] = 'admin_theme'
        return 'page'
