from framework.html_elements import FormElement, TableElement, ContainerElement, Label, Input
from framework.base_handlers import ContentHandler, RedirectMixIn
from framework.page import Page

__author__ = 'justusadam'


class LoginHandler(RedirectMixIn):

    def process_content(self):
        return Page(self._url, 'Login', ContainerElement(
            FormElement(
                TableElement(
                    [Label('Username', label_for='username'), Input(name='username', required=True)],
                    [Label('Password', label_for='password'), Input(input_type='password', required=True, name='password')]
                )
                , action='/login', classes={'login-form'})
        ))

    def process_post_query(self):
        pass