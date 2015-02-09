from dycm import theming
from dyc.util import decorators, structures
import dyc
from . import model, page
from dyc.util import html

__author__ = 'Justus Adam'
__version__ = '0.2'


class Common:
    def __init__(self, name, content, item_type):
        self.name = name
        self.content = content
        self.item_type = item_type



class RegionHandler:
    @dyc.inject_method('CommonsMap')
    def __init__(self, commons_map, region_name, region_config, theme, client):
        self.commons_map = commons_map
        self.client = client
        self.name = region_name
        self.theme = theme
        self.commons = self.get_all_commons(region_name, theme)
        self.config = region_config

    def get_all_commons(self, name, theme):
        region_info = model.Common.select().where(
                        model.Common.region == name,
                        model.Common.theme == theming.model.Theme.get(
                            machine_name=theme
                            )
                        )
        if region_info:
            return [
                self.get_item(model.CommonsConfig.get(
                    model.CommonsConfig.machine_name == a.machine_name),
                    a.render_args, a.show_title)
                for a in region_info
                ]
        else:
            return []

    def get_item(self, item:model.CommonsConfig, render_args, show_title):

        content = self.commons_map[item.element_type].compile(
                    item, render_args, show_title, self.client)

        return Common(item.machine_name, content, item.element_type)

    def wrap(self, value):
        classes = ['region', 'region-' + self.name.replace('_', '-')]
        if 'classes' in self.config:
            if isinstance(self.config['classes'], str):
                classes.append(self.config['classes'])
            else:
                classes += self.config['classes']
        return html.ContainerElement(
            html.ContainerElement(
                *value,
                classes={'region-wrapper', 'wrapper'}
                ),
            classes=set(classes)
            )

    def compile(self):
        stylesheets = []
        meta = []
        scripts = []
        cont_acc = []
        if self.commons:
            for item in self.commons:
                content = item.content
                if content:
                    stylesheets += content.stylesheets
                    meta += content.metatags
                    scripts += content.metatags
                    cont_acc.append(content.content)
            content = self.wrap(cont_acc)
        else:
            content = ''

        return page.Component(
            content,
            stylesheets=stylesheets,
            metatags=meta,
            scripts=scripts
            )


def add_regions(dc_obj):

    def _regions(client, theme):
        config = dc_obj.config['theme_config']['regions']
        return {region : RegionHandler(
                region,
                config[region],
                theme,
                client
                ).compile()
            for region in config
            }

    if not 'regions' in dc_obj.context:
        dc_obj.context['regions'] = _regions(
            dc_obj.request.client,
            dc_obj.config['theme']
            )

    return dc_obj


@decorators.apply_to_type(
    structures.DynamicContent,
    apply_before=False,
    return_from_decorator=False
    )
def Regions(dc_obj):
    theming.theme_dc_obj(dc_obj)
    add_regions(dc_obj)
