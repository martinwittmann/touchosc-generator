import base64
from typing import Dict

class MissingArgException(Exception):
    """A component argument was missing."""
    pass

class MissingDataException(Exception):
    """A data value was missing."""
    pass

class CustomJinjaFilters:
    def __init__(self, script_args):
        self.script_args = script_args

    def merge_jinja_dicts(self, *args):
        result = {}
        for dictionary in args:
            result = {**result, **dictionary}
        return result

    def base64_encode(self, text: str):
        return base64.b64encode(text.encode('utf-8')).decode('utf-8')

    def replace_placeholders(
        self, text: str = '', component: str = '', data: Dict = None, arguments: Dict = None, index: int = 0, column: int = 0, row: int = 0
    ):

        if type(text) != str:
            text = str(text)
        result = text

        try: 
            # Replace arguments if necessary.
            # We do that *before* the data values to allow using args in data.
            if arguments:
                result = self.replace_values('args', component, text, arguments, index, column, row)

            # Replace data values if necessary.
            if data:
                result = self.replace_values('data', component, result, data, index, column, row)


        except MissingArgException as err:
            if not self.script_args.ignore_missing_args:
                print(err)

            # Default to an empty string if a replacement/lookup failed.
            result = ''

        except MissingDataException as err:
            if not self.script_args.ignore_missing_data:
                print(err)

            # Default to an empty string if a replacement/lookup failed.
            result = ''

        # Replace loop variables.
        # Note that we use 1-based indexes for replacements, because for user-facing
        # We replace these values *after* handling data replacements because there we
        # need 0-based indexes and we don't want the replacements below to replace to
        # incorrect data indexes.
        # texts this makes much more sense.
        result = result.replace('@index_0', str(index))
        result = result.replace('@index', str(index + 1))
        result = result.replace('@column', str(column + 1))
        result = result.replace('@row', str(row + 1))

        return result

    def replace_values(self, data_type: str, component: str, text: str, data: Dict, item_index: int = 0, column: int = 0, row: int = 0):
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
                elif isinstance(tmp_data, list) and tmp_data[int(key)] is not None:
                    tmp_data = tmp_data[int(key)]
                else:
                    # We did not find the requested data.
                    if data_type == 'args':
                        raise MissingArgException(
                            'Missing argument "{text}" for component "{component}".'.format(
                                text=text, component=component
                            )
                        )
                    else:
                        raise MissingDataException(
                            'Missing data value "{text}" for component "{component}".'.format(
                                text=text, component=component
                            )
                        )

            if not isinstance(tmp_data, str) and not isinstance(tmp_data, int) and not isinstance(tmp_data, float):
                raise Exception(
                    'Value "{value}" for component {component} is not a string or number.'.format(
                        value=tmp_data,
                        component=component
                    )
                )

            # We found the data referenced in the string, replace it.
            result = result[0:start_index] + str(tmp_data) + result[end_index + 2 :]

            # Set data index to the next result, if any.
            start_index = result.find('{{' + data_type + '.')

        return result
