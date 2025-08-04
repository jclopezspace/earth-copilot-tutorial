import json
import os

# Get the current directory of the script
current_dir = os.path.dirname(os.path.abspath(__file__))

# load JSON data from file in the utils folder
with open(os.path.join(current_dir, 'open_veda_collections.json'), 'r', encoding='utf-8') as file:
    data = json.load(file)
 
# key to remove
key1 = 'assets'
key2 = "links"
key3 = "stac_extensions"
key4 = "links"
key5 = "item_assets"
key6 = "renders"
key7 = "summaries"
key8 = "stac_version"
key9 = "dashboard:is_periodic"
key10 = "dashboard:time_density"
key11 = "extent"
key12 = "license"
key13 = "cube:variables"
key14 = "cube:dimensions"
key15 = "type"
key16 = "providers"
key17 = "collection"
key18 = "data_type"
key19 = "dashboard:datetime_density"

def remove_key(d, key):
    if isinstance(d, dict):
        if key in d:
            del d[key]
        for v in d.values():
            remove_key(v,key)
    elif isinstance(d, list):
        for v in d:
            remove_key(v,key)

remove_key(data, key1)
remove_key(data, key2)
remove_key(data, key3)
remove_key(data, key4)
remove_key(data, key5)
remove_key(data, key6)
remove_key(data, key7)
remove_key(data, key8)
remove_key(data, key9)
remove_key(data, key10)
# remove_key(data, key11)
remove_key(data, key12)
remove_key(data, key13)
remove_key(data, key14)
remove_key(data, key15)
remove_key(data, key16)
remove_key(data, key17)
remove_key(data, key18)
remove_key(data, key19)

# pretty print on screen:
print(json.dumps(data, indent=4))

# saving the updated JSON data back to the file
with open(os.path.join(current_dir, 'open_veda_collections_minimized_with_extents.json'), 'w', encoding='utf-8') as file:
    json.dump(data, file, indent=2)
