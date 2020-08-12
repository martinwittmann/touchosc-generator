#!/usr/bin/env python3
# Compile dynamic templates to touch osc files.
import argparse
import os
import shutil
import sys
from typing import Dict, List

from lib.touchoscgenerate import get_description_data, generate_xml_from_description, file_output


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
    parser.add_argument('--ignore-missing-args', '-M', action='store_true', help='Ignore missing component arguments.')
    parser.add_argument('--ignore-missing-data', '-D', action='store_true', help='Ignore missing data values.')

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
