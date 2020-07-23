# TouchOsc Generator

A generator for [TouchOsc](https://hexler.net/products/touchosc) files which greatly reduces repetive tasks and adds several helpful features not available in the original [TouchOsc Editor](https://hexler.net/products/touchosc#downloads).

TouchOsc Generator does not have a UI, but a script generating .touchosc files based on input files (json) describing the TouchOsc interface you want to build.

If you don't have python installed or don't know how to run python scripts on your computer, in the [Installation](#installation) section you will find everything to get you started.

# Example
This created a basic .touchosc file containing just a label and some text in it.

example.json:
```
{
  "type": "layout",
  "mode": 3,
  "version": 17,
  "width": 2000,
  "height": 1200,
  "orientation": "horizontal",
  "tabpages": [
    {
      "type": "tabpage",
      "components": [
        {
          "type": "labelh",
          "text": "Hello world!",
          "x": "0",
          "y": "0",
          "width": "300",
          "height": "70"
        }
      ]
    }
  ]
}
```

```
python ./touchosc.py example.json
```
This creates ./output/example.touchosc.


## Installation
To run TouchOsc Generator you need to know how to run python scripts and have
python3 and the jinja2 package installed.

### Python installation
Follow the official installation instructions on https://wiki.python.org/moin/BeginnersGuide/Download.

### Pip (python package manager) installation
Please follow the installation instructions on https://pip.pypa.io/en/stable/installing

### Jinja2
To install jinja2 using pip, the following into a command line:

```pip install jinja2```