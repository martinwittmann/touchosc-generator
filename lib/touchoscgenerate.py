import json
import os
from typing import Dict, List
import zipfile

from jinja2 import Environment, FileSystemLoader

from lib.jinja2.customfilters import CustomJinjaFilters
from lib.jinja2.prependingloader import PrependingLoader


def get_description_data(description_file: str) -> Dict:
    # Parse components file
    with open(description_file, 'r') as description_file_handle:
        description_data = json.load(description_file_handle)
    return description_data


def generate_xml_from_description(description_data, script_args):
    # We always start with layout.xml, this is what the touchosc file format expects.
    template_name = 'layout.xml'
    template_file = os.path.join(script_args.templates_dir, template_name)

    if not os.path.isfile(template_file):
        raise FileNotFoundError('Template file ' + template_file + ' does not exist.')

    # The header defines all macros that we need.
    jinja2_env = Environment(loader=PrependingLoader(FileSystemLoader(script_args.templates_dir), '_header.xml'))

    filters = CustomJinjaFilters(script_args)
    jinja2_env.filters['b64encode'] =  filters.base64_encode
    jinja2_env.filters['placeholders'] =  filters.replace_placeholders
    jinja2_env.filters['merge'] = filters.merge_jinja_dicts

    # Provide the elements in data as global.
    if 'data' in description_data:
        jinja2_env.globals['data'] = description_data['data']
    else:
        jinja2_env.globals['data'] = None

    # Provide the elements in reusable_components as global.
    if 'reusable_components' in description_data:
        if 'data' in description_data:
            jinja2_env.globals['reusable_components'] = description_data['reusable_components']
        else:
            jinja2_env.globals['reusable_components'] = None

    template = jinja2_env.get_template(template_name)

    return template.render(component=description_data)


def file_output(data, output_name: str, output_dir, component_out: bool, no_zip_out: bool):
    # Always using index.xml since the is the only filename touchosc uses.
    components_file = os.path.join(output_dir, 'index.xml')
    output_file = os.path.join(output_dir, output_name + '.touchosc')

    if not os.path.isdir(output_dir):
        os.makedirs(output_dir)

    with open(components_file, 'w+') as file_handle:
        file_handle.write(data)

    if not no_zip_out:
        with zipfile.ZipFile(output_file, 'w') as zip_handle:
            zip_handle.write(os.path.basename(components_file))
            zip_handle.close()
    else:
        if os.path.isfile(output_file):
            os.remove(output_file)

    if not component_out:
        os.remove(components_file)
