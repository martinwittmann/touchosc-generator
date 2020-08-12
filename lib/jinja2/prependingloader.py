from jinja2 import BaseLoader, Environment, FileSystemLoader


# Copied from http://codyaray.com/2015/05/auto-load-jinja2-macros
class PrependingLoader(BaseLoader):
    def __init__(self, loader: FileSystemLoader, prepend_template: str) -> None:
        self.loader = loader
        self.prepend_template = prepend_template

    def get_source(self, environment: Environment, template: str):
        prepend_source, _, prepend_uptodate = self.loader.get_source(environment, self.prepend_template)
        main_source, main_filename, main_uptodate = self.loader.get_source(environment, template)
        uptodate = lambda: prepend_uptodate() and main_uptodate()
        return prepend_source + main_source, main_filename, uptodate

    def list_templates(self):
        return self.loader.list_templates()

