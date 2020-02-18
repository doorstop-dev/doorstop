from doorstop.core import find_item
from doorstop.common import DoorstopWarning
import os 

def find(args, cwd):
    """Find Item and display path and line of refernce on console""" 
    item = find_item(args.UID)

    if args.directory:
        references = item.find_ref(paths(args.directory))

    else:
        references = item.find_ref()



    if isinstance(references,tuple):
         print(f'\nError: no reference found in item {args.UID}')
    else:
        keys = references.keys()

        print(f'\nThere are {len(keys)} references found for the UID {item.uid}:\n')
        
        for key,value in references.items():
            print(f'ref: {key}')
            print(f'path&line: {value}')
  

# Function to get all ppates from the input directory
def paths(directory):
    """Yield  paths from input directory"""
    path_cache = []
    for dirpath, _, filenames in os.walk(directory):
        for filename in filenames:
            path = os.path.join(dirpath, filename)
            # # Skip ignored paths
            # if self.ignored(path):
            #     continue
            # Skip hidden paths
            if os.path.sep + '.' in path:
                continue
            relpath = os.path.relpath(path)
            path_cache.append((path, filename, relpath))
    # yield from entfernt da path_cache sowieso in einer liste gespeichert wurde dadurch sind alle vorteile des memory managements
    #bereits verloren und die liste kann auch normal übergeben werden. Das erleichtert widerholtes iterrierne über sie.... 

    #yield from path_cache

    return path_cache

  

    

   


    

   
