import json

current_dir = os.path.dirname(os.path.abspath(__file__))
in_file_path = os.path.join(current_dir, 'open_veda_collections_minimized_with_extents.json')

with open(in_file_path,'r') as in_json_file:

    # Read the file and convert it to a dictionary
    json_obj_list = json.load(in_json_file)

    for json_obj in json_obj_list:
        filename=json_obj['id']+'.json'

        with open(filename, 'w') as out_json_file:
            # Save each obj to their respective filepath
            # with pretty formatting thanks to `indent=4`
            json.dump(json_obj, out_json_file, indent=4)