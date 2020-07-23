#!/usr/bin/python
# Compile dynamic templates to touch osc files.
import sys, os, base64, shutil, json
from jinja2 import Environment, FileSystemLoader, BaseLoader



# Copied from http://codyaray.com/2015/05/auto-load-jinja2-macros
class PrependingLoader(BaseLoader):
  def __init__(self, delegate, prepend_template):
    self.delegate = delegate
    self.prepend_template = prepend_template

  def get_source(self, environment, template):
    prepend_source, _, prepend_uptodate = self.delegate.get_source(environment, self.prepend_template)
    main_source, main_filename, main_uptodate = self.delegate.get_source(environment, template)
    uptodate = lambda: prepend_uptodate() and main_uptodate()
    return prepend_source + main_source, main_filename, uptodate

  def list_templates(self):
    return self.delegate.list_templates()


def merge_jinja_dicts(*args):
  result = {}
  for dictionary in args:
    result = {**result, **dictionary}
  return result


def base64_encode(text):
  return base64.b64encode(text.encode('utf-8')).decode('utf-8')

def replace_placeholders(text='', data=False, arguments=False, index=0, column=0, row=0):
  if (type(text) != str):
    text = str(text)
  result = text

  # Retrieve data values if necessary.
  if data:
    start_index = result.find('{{data.')
    while start_index > -1:
      end_index = start_index + result[start_index:].find('}}')
      if (end_index < 0):
        # Stop if we don't find any end delimiters.
        break
      data_str = result[start_index + 7:end_index]
      data_keys = data_str.split('.')
      tmp_data = data
      for key in data_keys:
        # Replace index values with 0-based indexes.
        if key == '@index':
          key = index
        elif key == '@column':
          key = column
        elif key == '@row':
          key = row

        if isinstance(tmp_data, dict) and key in tmp_data:
          tmp_data = tmp_data[key]
        elif isinstance(tmp_data, list) and tmp_data[key]:
          tmp_data = tmp_data[key]
        else:
          # Something went wrong, we did not find the requested data.
          # TODO Error handling.
          print('Error looking up data: ' + result[start_index + 2:end_index] + ' was not found. Last key: "' + str(key) + '"')
          return result

      if not isinstance(tmp_data, str) and not isinstance(tmp_data, int) and not isinstance(tmp_data, float):
        print('Error looking up data: ' + result[start_index + 2:end_index] + ' is not a string or number. Last key: ' + str(key) + " Type: " + str(type(tmp_data)))
        return result

      # We found the data referenced in the string, replace it.
      result = result[0:start_index] + str(tmp_data) + result[end_index + 2:]

      # Set data index to the next result, if any.
      start_index = result.find('{{data.')


  # Replace arguments if necessary.
  if arguments:
    start_index = result.find('{{args.')
    while start_index > -1:
      end_index = start_index + result[start_index:].find('}}')
      if (end_index < 0):
        # Stop if we don't find any end delimiters.
        break
      arg_str = result[start_index + 7:end_index]
      arg_keys = arg_str.split('.')
      tmp_arg = arguments
      for key in arg_keys:
        if isinstance(tmp_arg, dict) and key in tmp_arg:
          tmp_arg = tmp_arg[key]
        elif isinstance(tmp_arg, list) and tmp_arg[key]:
          tmp_arg = tmp_arg[key]
        else:
          # Something went wrong, we did not find the requested arg.
          # TODO Error handling.
          print('Error looking up argument: ' + result[start_index + 2:end_index] + ' was not found. Last key: "' + str(key) + '"')
          return result

      if not isinstance(tmp_arg, str) and not isinstance(tmp_arg, int) and not isinstance(tmp_arg, float):
        print('Error looking up arg: ' + result[start_index + 2:end_index] + ' is not a string or number. Last key: ' + str(key) + " Type: " + str(type(tmp_arg)))
        return result

      # We found the arg referenced in the string, replace it.
      result = result[0:start_index] + str(tmp_arg) + result[end_index + 2:]

      # Set arg index to the next result, if any.
      start_index = result.find('{{arg.')

  # Replace loop variables.
  # Note that we use 1-based indexes for replacements, because for user-facing
  # We replace these values *after* handling data replacements because there we
  # need 0-based indexes and we don't want the replacements below to replace to
  # incorrect data indexes.
  # texts this makes much more sense.
  result = result.replace("@index", str(index + 1))
  result = result.replace('@column', str(column + 1))
  result = result.replace('@row', str(row + 1))

  return result





if (len(sys.argv) < 2):
  print("Usage: ./touchosc.py [components-file]\nSee example.json.")
  sys.exit(1)

components_file = sys.argv[1]
output_name = os.path.splitext(os.path.basename(components_file))[0]

with open(components_file, 'r') as components_data_file_handle:
  components_data = json.load(components_data_file_handle)


template_dir = os.path.abspath('templates/') + '/'
output_dir = 'output/' + output_name

# We always start with layout.xml, this is whatthe touchosc file format expects.
template_name = 'layout.xml'
template_file = template_dir + template_name

# Create the output dir for this components file if not existing.
if (not os.path.isdir(output_dir)):
  os.mkdir(output_dir)

# Always using index.html since the is the only filename touchosc uses.
output_file = os.path.abspath(output_dir + '/index.xml')

if (not os.path.isfile(template_file)):
  print("Template file " + template_file + " does not exist.")
  sys.exit(1)


  
# The header defines all macros that we need.
jinja2_environment = Environment(
  loader=PrependingLoader(FileSystemLoader(template_dir), '_header.xml')
)
jinja2_environment.filters['b64encode'] = base64_encode
jinja2_environment.filters['placeholders'] = replace_placeholders
jinja2_environment.filters['merge'] = merge_jinja_dicts

# Provide the elements in data as global.
if ('data' in components_data):
  jinja2_environment.globals['data'] = components_data['data']
else:
  jinja2_environment.globals['data'] = False

# Provide the elements in reusable_components as global.
if ('reusable_components' in components_data):
  if ('data' in components_data):
    jinja2_environment.globals['reusable_components'] = components_data['reusable_components']
  else:
    jinja2_environment.globals['reusable_components'] = False


template = jinja2_environment.get_template(template_name)

output = template.render(component=components_data)
file_handle = open(output_file, 'w+')
file_handle.write(output)
file_handle.close()


shutil.make_archive(output_file, 'zip', output_dir)
# Note that output_dir already contains the output_name we want.
# This means we can simply add the .touchosc extension and get the filename we want.
# Example: ./touchosc.py test.json -> output/test -> output/test.touchosc.

# TODO Remove this.
#os.rename(output_file + '.zip', output_dir + ".touchosc")
os.rename(output_file + '.zip', "/home/witti/test.touchosc")