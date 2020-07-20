#!/usr/bin/python
# Compile dynamic templates to touch osc files.
import sys, os, base64, shutil, json
from jinja2 import Environment, FileSystemLoader

def s(str):
  return base64.b64encode(str)





if (len(sys.argv) < 2):
  print("Usage: ./touchosc.py [components-file]\nSee example.json.")
  sys.exit(1)

components_file = sys.argv[1]
output_name = os.path.splitext(components_file)[0]

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


  
env = Environment(
  loader=FileSystemLoader(template_dir),
)

template = env.get_template(template_name)

"""
layout = {
  'width': 2000,
  'height': 1200,
  'column_spacer': 20,
  'right': {
    'width': 400,
    'spacer': 10,
    'button_height': 130,
    'button_height_sm': 70,
    'button_width': 400,
    'button_half_width': 195,
    'tempo_y': 601,
  },
}
layout['right']['x'] = layout['width'] - layout['right']['width'] - layout['column_spacer']

data = {
  'label_1': s('Gallo Wuttu'),
  'toggle_click': {
    'text': s('CLICK MUTE'),
  },
  'buttons': {
    'decrease_tempo': {
      'name': s('decrease_tempo'),
      'width': layout['right']['button_half_width'],
      'height': layout['right']['button_height_sm'],
      'x': layout['right']['x'],
      'y': layout['right']['tempo_y'],
      'color': 'orange',
      'osc': s('/a/41130'),
      'type': 'push',
      'local_off': 'false',
      'sp': 'true',
      'sr': 'false',
    },
    'decrease_tempo_label': {
      'name': s('decrease_tempo_label'),
      'text': s('-'),
      'y': layout['right']['tempo_y'] - 5,
      'type': 'labelh',
      'background': 'false',
      'outline': 'false',
      'color': 'gray',
      'size': '75',
    },
    'increase_tempo': {
      'name': s('increase_tempo'),
      'width': layout['right']['button_half_width'],
      'height': layout['right']['button_height_sm'],
      'x': layout['right']['x'] + layout['right']['button_half_width'] + layout['right']['spacer'],
      'y': layout['right']['tempo_y'],
      'color': 'orange',
      'osc': s('/a/41129'),
      'type': 'push',
      'local_off': 'false',
      'sp': 'true',
      'sr': 'false',
    },
    'increase_tempo_label': {
      'name': s('increase_tempo_label'),
      'text': s('+'),
      'type': 'labelh',
      'background': 'false',
      'outline': 'false',
      'color': 'gray',
      'size': '65',
    },
    'record': {
      'name': s('record'),
      'width': layout['right']['button_width'],
      'height': layout['right']['button_height'],
      'x': layout['right']['x'],
      'y': 1014,
      'color': 'red',
      'osc': s('/record'),
      'type': 'push',
      'local_off': 'false',
      'sp': 'true',
      'sr': 'false',
    },
  },
}

"""
output = template.render(component=components_data)
file_handle = open(output_file, 'w+')
file_handle.write(output)
file_handle.close()


shutil.make_archive(output_file, 'zip', output_dir)
# Note that output_dir already contains the output_name we want.
# This means we can simply add the .touchosc extension and get the filename we want.
# Example: ./touchosc.py test.json -> output/test -> output/test.touchosc.
os.rename(output_file + '.zip', output_dir + ".touchosc")