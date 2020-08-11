#!/usr/bin/env python3
# Compile dynamic templates to touch osc files.
import argparse
import base64
import json
import os
import shutil
import sys
import zipfile
from typing import Dict, List, Literal, Tuple, Union

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


def merge_jinja_dicts(*args):
    result = {}
    for dictionary in args:
        result = {**result, **dictionary}
    return result


def base64_encode(text: str):
    return base64.b64encode(text.encode('utf-8')).decode('utf-8')


def retrieve(data_type: Literal['data', 'args'], text: str, data: Dict, item_index: int = 0, column: int = 0, row: int = 0):
    result = text

    start_index = result.find('{{' + data_type + '.')
    while start_index > -1:
        end_index = start_index + result[start_index:].find('}}')
        if end_index < 0:
            # Stop if we don't find any end delimiters.
            # TODO Error handling.
            break
        data_str = result[start_index + 7 : end_index]
        data_keys = data_str.split('.')
        tmp_data = data
        for key in data_keys:
            # Replace index values with 0-based indexes.
            if key == '@index':
                key = item_index
            elif key == '@column':
                key = column
            elif key == '@row':
                key = row

            if isinstance(tmp_data, dict) and key in tmp_data:
                tmp_data = tmp_data[key]
            elif isinstance(tmp_data, list) and tmp_data[key] is not None:
                tmp_data = tmp_data[key]
            else:
                # Something went wrong, we did not find the requested data.
                # TODO Error handling.
                print(
                    'Error looking up {type}: {data} was not found. Last key: "{key}"'.format(
                        type=data_type, data=result[start_index + 2 : end_index], key=str(key)
                    )
                )
                return result

        if not isinstance(tmp_data, str) and not isinstance(tmp_data, int) and not isinstance(tmp_data, float):
            print(
                'Error looking up {type}: {data} is not a string or number. Last key: "{key}" Type: {data_type}'.format(
                    type=data_type,
                    data=result[start_index + 2 : end_index],
                    key=str(key),
                    data_type=str(type(tmp_data)),
                )
            )
            return result

        # We found the data referenced in the string, replace it.
        result = result[0:start_index] + str(tmp_data) + result[end_index + 2 :]

        # Set data index to the next result, if any.
        start_index = result.find('{{data.')

    return result


def replace_placeholders(
    text: str = '', data: Dict = None, arguments: Dict = None, index: int = 0, column: int = 0, row: int = 0
):
    if type(text) != str:
        text = str(text)
    result = text

    # Retrieve data values if necessary.
    if data:
        result = retrieve('data', text, data, index, column, row)

    # Replace arguments if necessary.
    if arguments:
        result = retrieve('args', result, arguments, index, column, row)

    # Replace loop variables.
    # Note that we use 1-based indexes for replacements, because for user-facing
    # We replace these values *after* handling data replacements because there we
    # need 0-based indexes and we don't want the replacements below to replace to
    # incorrect data indexes.
    # texts this makes much more sense.
    result = result.replace('@index', str(index + 1))
    result = result.replace('@column', str(column + 1))
    result = result.replace('@row', str(row + 1))

    return result


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
    jinja2_environment = Environment(loader=PrependingLoader(FileSystemLoader(script_args.templates_dir), '_header.xml'))
    jinja2_environment.filters['b64encode'] = base64_encode
    jinja2_environment.filters['placeholders'] = replace_placeholders
    jinja2_environment.filters['merge'] = merge_jinja_dicts

    # Provide the elements in data as global.
    if 'data' in description_data:
        jinja2_environment.globals['data'] = description_data['data']
    else:
        jinja2_environment.globals['data'] = None

    # Provide the elements in reusable_components as global.
    if 'reusable_components' in description_data:
        if 'data' in description_data:
            jinja2_environment.globals['reusable_components'] = description_data['reusable_components']
        else:
            jinja2_environment.globals['reusable_components'] = None

    template = jinja2_environment.get_template(template_name)

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


def main(argv: List[str]):
    # Remove potential empty strings from the arguments as they confuse argparse
    argv = list(filter(lambda elem: elem != '', argv))

    # Parse command line parameters
    parser = argparse.ArgumentParser(prog='touchosc.py', description='Compile dynamic templates to touch osc files.',)
    parser.add_argument('description_file', help='JSON file containing the description of the components.')
    parser.add_argument('--name', '-n', help='Name of output file. Default: <description_file>.touchosc')
    parser.add_argument('--output-dir', '-o', help='Output directory. Default: ./')
    parser.add_argument(
        '--create-components-file',
        '-c',
        action='store_true',
        help='Create unzipped index.xml file for further processing.',
    )
    parser.add_argument('--no-zipped-output', '-z', action='store_true', help='Do not create zipped .touchosc file.')
    parser.add_argument('--templates-dir', '-t', help='Location of templates directory. Default: templates/ in the same directory as touchosc.py.')

    # Remove first argument, which is always the path to this script.
    # Argparse expects this to be removed, when not using the default params.
    args = parser.parse_args(argv[1:])

    # Sanitize input
    args.description_file = os.path.abspath(args.description_file)
    if not os.path.isfile(args.description_file):
        print('Description file ' + args.description_file + ' does not exist', file=sys.stderr)
        sys.exit(1)

    if args.name is None:
        args.name = os.path.splitext(os.path.basename(args.description_file))[0]

    if args.output_dir is None:
        args.output_dir = os.path.dirname(args.description_file)

    if args.templates_dir is None:
        args.templates_dir = os.path.join(os.path.abspath(os.path.dirname(argv[0])), 'templates')

    try:
        components_data = get_description_data(args.description_file)
    except OSError as e:
        print('Description file ' + e.filename + ' could not be opened.', file=sys.stderr)
        sys.exit(1)

    output = generate_xml_from_description(components_data, script_args=args)

    try:
        file_output(output, args.name, args.output_dir, args.create_components_file, args.no_zipped_output)
    except OSError as e:
        print(e.filename + ' could not be opened.', file=sys.stderr)


if __name__ == '__main__':
    main(sys.argv)
