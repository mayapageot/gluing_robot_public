import json
import os
import shutil
import numpy as np

def create_dictionary(path_daughter: str):
    '''keys_init = ['cryostat', "run", 'measurement', "channel", "number_file", 'window_point', "mean_pulse_min", 'mean_pulse_max',
            'mean_pulse_sample', 'baseline_sample', 'sigma_baseline', 'inc_sigma_baseline', 'threshold',
            'max_search_jitter', 'delay', 'path_heat_channel', 'filename']'''
    keys_init = ["filename"]
    try :
        dictionary = load_dict(path_daughter+'dictionary.json')
        keys = [key for key in keys_init if key not in dictionary.keys()]
    except FileNotFoundError:
        dictionary = {'path': path_daughter}
        keys = keys_init
    print(dictionary)
    bool_merge = 'path_heat_channel' not in dictionary.keys()
    for key in keys:
        value = input(key + ': ')
        if key == 'sigma_baseline':
            print(5*value)
        try:
            dictionary[key] = float(value)
        except ValueError:
            dictionary[key] = value
    with open(path_daughter + 'dictionary.json', 'w') as json_file:
        json.dump(dictionary, json_file, indent=4)


def get_dictionary_name(path):
    list_files = os.listdir(path)
    filtered_files = [file for file in list_files if file.endswith("dictionary.json")]
    if filtered_files:
        return filtered_files[0]
    else:
        print('create the dictionary first !')
        raise FileNotFoundError


def load_dict(path: str) -> dict:
    dict_name = get_dictionary_name(path)
    with open(path + dict_name, 'r') as json_file:
        dictionary = json.load(json_file)
    return dictionary


def update_dict(path: str, new_dict: dict):
    dict_path = path + get_dictionary_name(path)
    dictionary = load_dict(path)
    for key in new_dict:
        if isinstance(new_dict[key], np.ndarray):
            new_dict[key]=list(new_dict[key])
    dictionary.update(new_dict)
    with open(dict_path, 'w') as json_file:
        json.dump(dictionary, json_file, indent=4)


def check_keynames(path, key_list: list, typ=float):
    dictionary = load_dict(path)
    key_values = []
    if type(key_list) == str :
        key_list = [key_list]
    for key in key_list :
        try :
            key_value = dictionary[key]
        except KeyError:
            key_value = typ(input(key+': '))
            update_dict(path, {key: key_value})
        key_values.append(key_value)
    return key_values

def save_dict(dict_path, dictionary):
    try:
        update_dict(dict_path, dictionary)
    except FileNotFoundError:
        with open(dict_path, 'w') as json_file:
            json.dump(dictionary, json_file, indent=4)


def get_values(dictionary: dict, key_list: list) -> list:
    return [dictionary[key] for key in key_list]


def get_value_with_path(path,key_list):
    return get_values(load_dict(path),key_list)


def get_keys_starting_with(dictionary, sequence):
    return [key for key in dictionary.keys() if key.startswith(sequence)]


def list_files_in_directories(directory_path):
    for dirpath, dirnames, filenames in os.walk(directory_path):
        for dirnames in dirnames:
            path = os.path.join(dirpath, dirnames)
            A = path.split("/")
            A[-2] = "meas3"
            B = '/'.join(A)+'/'
            list_files = os.listdir(path)
            for file in list_files:
                shutil.move(os.path.join(path, file), B)


if __name__ == "__main__":
    path_daughter = '/Users/mp274748/Documents/data_arg/RUN97/measu3'
    list_files_in_directories(path_daughter)
