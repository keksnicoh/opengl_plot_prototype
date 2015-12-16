import re

def import_data_file(file_path, seperator=','):
    pattern = re.compile('[^0-9.*-^+^/]+')
    with open(file_path, 'r') as data_file:
        data = data_file.read().replace("^", "**").split(seperator)
        data_set = range(len(data))
        for i, data_point in enumerate(data):
            data_set[i] = eval(pattern.sub('', data_point))
        return data_set
    return None


