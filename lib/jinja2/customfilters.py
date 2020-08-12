import base64
from typing import Dict

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
        self, component: str = '', text: str = '', data: Dict = None, arguments: Dict = None, index: int = 0, column: int = 0, row: int = 0
    ):
        if type(text) != str:
            text = str(text)
        result = text

        # Retrieve data values if necessary.
        if data:
            result = self.get_replacement_value('data', component, text, data, index, column, row)

        # Replace arguments if necessary.
        if arguments:
            result = self.get_replacement_value('args', component, result, arguments, index, column, row)

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

    def get_replacement_value(self, data_type: str, component: str, text: str, data: Dict, item_index: int = 0, column: int = 0, row: int = 0):
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
                        'Can\'t find "{text}" for component "{component}"'.format(
                            text=text, component=component
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
