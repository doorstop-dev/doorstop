"""Representation of an item in a document."""

import os
import re
import functools

import pyficache

from doorstop import common
from doorstop.common import DoorstopError, DoorstopWarning, DoorstopInfo
from doorstop.core.base import (add_item, edit_item, delete_item,
                                auto_load, auto_save,
                                BaseValidatable, BaseFileObject)
from doorstop.core.types import Prefix, UID, Text, Level, Stamp, to_bool, REF #added REF
from doorstop.core import editor
from doorstop import settings

log = common.logger(__name__)


def requires_tree(func):
    """Decorator for methods that require a tree reference."""
    @functools.wraps(func)
    def wrapped(self, *args, **kwargs):
        """Wrapped method that requires a tree reference."""
        if not self.tree:
            name = func.__name__
            log.critical("`{}` can only be called with a tree".format(name))
            return None
        return func(self, *args, **kwargs)
    return wrapped


def requires_document(func):
    """Decorator for methods that require a document reference."""
    @functools.wraps(func)
    def wrapped(self, *args, **kwargs):
        """Wrapped method that requires a document reference."""
        if not self.document:
            name = func.__name__
            msg = "`{}` can only be called with a document".format(name)
            log.critical(msg)
            return None
        return func(self, *args, **kwargs)
    return wrapped


class Item(BaseValidatable, BaseFileObject):  # pylint: disable=R0902

    """Represents an item file with linkable text."""

    EXTENSIONS = '.yml', '.yaml'

    DEFAULT_LEVEL = Level('1.0')
    DEFAULT_ACTIVE = True
    DEFAULT_NORMATIVE = True
    DEFAULT_DERIVED = False
    DEFAULT_REVIEWED = Stamp()
    DEFAULT_TEXT = Text()
    DEFAULT_REF = ""
                                        # add 02.12.2019
    DEFAULT_Is_Req = True       

    DEFAULT_SPEC_RATIONALE = Text()
    DEFAULT_SPEC_STATUS = "In_Analysis"
    DEFAULT_SPEC_SHORT_DECRIPTION = ""
    DEFAULT_SPEC_ID = ""
    DEFAULT_SPEC_VERSION = 1
    DEFAULT_Assumption = ""
    DEFAULT_Ad_Info = ""
    DEFAULT_Author = ""
    DEFAULT_Generation = "Manual"
    DEFAULT_REFINE = ""
    DEFAULT_ASSOCIATED = ""
    DEFAULT_Validation_Ref = ""
    DEFAULT_Validation_Mean = "Review"
    DEFAULT_Verification_Ref = ""
    DEFAULT_Verification_Mean = "LAB_TEST"
    DEFAULT_Verification_Rationale = ""
    DEFAULT_Verification_Status = "Analysis"
    DEFAULT_VoV_Ref = ""
    DEFAULT_Alllocation = ""

                                        # end add 

                                        # add 15.01.2020
    DEFAULT_SIDEBAR=''
    DEFAULT_EXTENSION=''
    DEFAULT_TITLE=''
                                        # end add 


    

    def __init__(self, path, root=os.getcwd(), **kwargs):
        """Initialize an item from an existing file.

        :param path: path to Item file
        :param root: path to root of project

        """
        super().__init__()
        # Ensure the path is valid
        if not os.path.isfile(path):
            raise DoorstopError("item does not exist: {}".format(path))
        # Ensure the filename is valid
        filename = os.path.basename(path)
        name, ext = os.path.splitext(filename)
        try:
            UID(name).check()
        except DoorstopError:
            msg = "invalid item filename: {}".format(filename)
            raise DoorstopError(msg) from None
        # Ensure the file extension is valid
        if ext.lower() not in self.EXTENSIONS:
            msg = "'{0}' extension not in {1}".format(path, self.EXTENSIONS)
            raise DoorstopError(msg)
        # Initialize the item
        self.path = path
        self.root = root
        self.document = kwargs.get('document')
        self.tree = kwargs.get('tree')
        self.auto = kwargs.get('auto', Item.auto)
        # Set default values
        self._data['level'] = Item.DEFAULT_LEVEL
        self._data['active'] = Item.DEFAULT_ACTIVE
        self._data['normative'] = Item.DEFAULT_NORMATIVE
        self._data['derived'] = Item.DEFAULT_DERIVED
        self._data['reviewed'] = Item.DEFAULT_REVIEWED
        self._data['text'] = Item.DEFAULT_TEXT
        self._data['ref'] = set()
        self._data['links'] = set()



                                                # add 02.12.2019 / 06.12.2019
        self._data['Is_Req'] = Item.DEFAULT_Is_Req

        self._data['SPEC_RATIONALE'] = Item.DEFAULT_SPEC_RATIONALE
        self._data['SPEC_SHORT_DECRIPTION'] = Item.DEFAULT_SPEC_SHORT_DECRIPTION 
        self._data['SPEC_ID'] = Item.DEFAULT_SPEC_ID
        self._data['SPEC_VERSION'] = Item.DEFAULT_SPEC_VERSION
        #self._data['SPEC_TEXT'] = Item.DEFAULT_SPEC_TEXT
        self._data['Assumption'] = Item.DEFAULT_Assumption
        self._data['Add_Info'] = Item.DEFAULT_Ad_Info
        self._data['Author'] = Item.DEFAULT_Author
        self._data['Generation'] = Item.DEFAULT_Generation
        self._data['REFINE'] = Item.DEFAULT_REFINE
        self._data['ASSOCIATED'] = Item.DEFAULT_ASSOCIATED
        self._data['SPEC_STATUS'] = Item.DEFAULT_SPEC_STATUS
        self._data['Validation_Ref'] = Item.DEFAULT_Validation_Ref
        self._data['Validation_Mean'] = Item.DEFAULT_Validation_Mean
        self._data['Verification_Ref'] = Item.DEFAULT_Verification_Ref
        self._data['Verification_Mean'] = Item.DEFAULT_Verification_Mean
        self._data['Verification_Rationale'] = Item.DEFAULT_Verification_Rationale
        self._data['Verification_Status'] = Item.DEFAULT_Verification_Status
        self._data['VoV_Ref'] = Item.DEFAULT_VoV_Ref
        self._data['Allocation'] = Item.DEFAULT_Alllocation

        # add 15.01.2020
        # Hinzufügen von attributen die nur auftreten wenn es sich bei dem yaml file nicht um ein requirmenet sondern
        # um eine Beschreibung überschrift oder sonstiges handelt... 
        self._NO_REQ_data['EXTENSION']= Item.DEFAULT_EXTENSION
        self._NO_REQ_data['TITLE']=Item.DEFAULT_TITLE
        self._NO_REQ_data['SIDEBAR']= Item.DEFAULT_SIDEBAR
        # end add 
        
        
                                                # end add 

    def __repr__(self):
        return "Item('{}')".format(self.path)

    def __str__(self):
        if common.verbosity < common.STR_VERBOSITY:
            return str(self.uid)
        else:
            return "{} ({})".format(self.uid, self.relpath)

    def __lt__(self, other):
        if self.level == other.level:
            return self.uid < other.uid
        else:
            return self.level < other.level

    @staticmethod
    @add_item
    def new(tree, document, path, root, uid, level=None, auto=None):  # pylint: disable=R0913
        """Internal method to create a new item.

        :param tree: reference to the tree that contains this item
        :param document: reference to document that contains this item

        :param path: path to directory for the new item
        :param root: path to root of the project
        :param uid: UID for the new item

        :param level: level for the new item
        :param auto: automatically save the item

        :raises: :class:`~doorstop.common.DoorstopError` if the item
            already exists

        :return: new :class:`~doorstop.core.item.Item`

        """
        UID(uid).check()
        filename = str(uid) + Item.EXTENSIONS[0]
        path2 = os.path.join(path, filename)
        # Create the initial item file
        log.debug("creating item file at {}...".format(path2))
        Item._create(path2, name='item')
        # Initialize the item
        item = Item(path2, root=root, document=document, tree=tree, auto=False)    
        item.level = level if level is not None else item.level
        if auto or (auto is None and Item.auto):
            item.save()
        # Return the item
        return item

    def load(self, reload=False):
        """Load the item's properties from its file."""
        if self._loaded and not reload:
            return
        log.debug("loading {}...".format(repr(self)))
        # Read text from file
        text = self._read(self.path)
        # Parse YAML data from text
        data = self._load(text, self.path)

        # Store parsed data
        # Herrausfinden on das YMAL file ein Requirement ist oder nicht...
        # Danach darus schlussfolgern welche attribute in dem file auftauche sollen und welche nicht 15.01.2020
        # Als erstes wird geschaut ob das data dictionary überhaupt daten entält ....
        if bool(data):
            if  data['Is_Req']:

                # tmp list to check for values that are only displayed when item is not a requirement ...
                tmp_list= ['EXTENSION','TITLE','SIDEBAR']


                for key, value in data.items():
                   
                    #Is_Req add => vllt später anders um andere attribute zu sperren 09.01.2020
                    if key == 'Is_Req':
                        values = to_bool(value)
                    #end Is_Req add
                    if key == 'level':
                        value = Level(value)
                    elif key == 'active':
                        value = to_bool(value)
                    elif key == 'normative':
                        value = to_bool(value)
                    elif key == 'derived':
                        value = to_bool(value)
                    elif key == 'reviewed':
                        value = Stamp(value)    
                    elif key == 'text':
                        #changed behhaviour of Text class in types.py to let linebreaks in ...
                        value = Text(value)
                    # add 02.12.2019
                    elif key == 'SPEC_RATIONALE':
                        value = Text(value)
                    elif key == 'SPEC_STATUS':
                        value = Text(value)
                                                # end add 

                                                # add 09.12.2019
                    elif key == 'ref':            
                        value = set(REF(part) for part in value)
                        # print(value)
                                                # end add
                    elif key == 'links':
                        # print(type(value))
                        value = set(UID(part) for part in value)
                        # print(type(value))
                        # print(value)
                    elif key in tmp_list:
                            continue
                        
                    else:
                        if isinstance(value, str):
                            value = Text(value)

                    self._data[key] = value
            # add 15.01.2020
            else:

                for key, value in data.items():
                    
                    if key == 'Is_Req':
                        values = to_bool(value)
                        self._data[key] = value

                    elif key == 'level':
                        value = Level(value)
                        self._data[key] = value

                    elif key == 'text':
                        value = Text(value)
                        self._data[key] = value


                    elif key == 'EXTENSION':
                        value=Text(value.upper())
                        self._NO_REQ_data[key] = value
                    elif key == 'TITLE':
                        value = Text(value)
                        self._NO_REQ_data[key] = value
                    elif key == 'SIDEBAR':
                        value =Text(value)
                        self._NO_REQ_data[key] = value
                    else:
                        # format not know
                        # will not be therer anymore after this procedure
                        continue                               
                        
        # Set meta attributes
        self._loaded = True#

    @edit_item
    def save(self):
        """Format and save the item's properties to its file."""
        log.debug("saving {}...".format(repr(self)))
        # Format the data items
        data = self.data      
        # Dump the data to YAML    
        text = self._dump(data)
        # Save the YAML to file
        self._write(text, self.path)
        # Set meta attributes
        self._loaded = False
        self.auto = True

    # properties #############################################################

   # add 09.12.2020 change behaviour for yaml dumping if file is not a requirement
    @property
    @auto_load
    def data(self):
        """Get all the item's data formatted for YAML dumping."""
        data = {}
       
        data['Is_Req'] = self._data['Is_Req']
   
        if data['Is_Req'] == True:

            for key, value in self._data.items():
            
                if key == 'level':
                    value = value.yaml
                elif key == 'text':       
                    value = value.yaml     
                elif key == 'ref':
                    # add 11.12.2019
                    value = [{str(i): i.stamp.yaml} for i in sorted(value)] #####here
                    #end add 
                elif key == 'links':
                    value = [{str(i): i.stamp.yaml} for i in sorted(value)]
                elif key == 'reviewed':
                    value = value.yaml
                    # print(f'Value aus YAML: {value}')
                else:
                    
                    if isinstance(value, str):
                        # length of "key_text: value_text"
                        length = len(key) + 2 + len(value)
                        if length > settings.MAX_LINE_LENGTH or '\n' in value:
                            value = Text.save_text(value)
                        else:
                            value = str(value)  # line is short enough as a strig

                # add 09.12.2020 change behaviour for yaml dumping if file is not a requirement
                if not key == 'Is_Req':
                    data[key] = value
         
            
        else:
           
            for key, value in self._data.items():
            
                if key == 'text':
                    value = value.yaml
                    data[key] = value

                elif key == 'level':
                    value = value.yaml
                    data[key] = value

                elif key == 'Is_Req':
                    value = to_bool(value)
                    data[key] = value             

            # Check Attribute die nicht vorhanden sind wenn item ein requirment ist
            for key, value in self._NO_REQ_data.items():
                if key == 'TITLE':
                    length = len(key) + 2 + len(value)
                    if length > settings.MAX_LINE_LENGTH or '\n' in value:
                        value = Text.save_text(value)
                    else:
                        value = str(value)  # line is short enough as a strig

                    data[key] = value

                elif key == 'EXTENSION':
                    length = len(key) + 2 + len(value)
                    if length > settings.MAX_LINE_LENGTH or '\n' in value:
                        value = Text.save_text(value)
                    else:
                        value = str(value)  # line is short enough as a strig

                    data[key] = value

                elif key == 'SIDEBAR':
                    length = len(key) + 2 + len(value)
                    if length > settings.MAX_LINE_LENGTH or '\n' in value:
                        value = Text.save_text(value)
                    else:
                        value = str(value)  # line is short enough as a strig

                    data[key] = value
                
        
        return data

        #end add 

    @property
    def uid(self):
        """Get the item's UID."""
        filename = os.path.basename(self.path)
        return UID(os.path.splitext(filename)[0])

    @property
    def prefix(self):
        """Get the item UID's prefix."""
        return self.uid.prefix

    @property
    def number(self):
        """Get the item UID's number."""
        return self.uid.number

    @property
    @auto_load
    def level(self):
        """Get the item's level."""
        return self._data['level']

    @level.setter
    @auto_save
    @auto_load
    def level(self, value):
        """Set the item's level."""
        self._data['level'] = Level(value)

    @property
    def depth(self):
        """Get the item's heading order based on it's level."""
        return len(self.level)

    @property
    @auto_load
    def active(self):
        """Get the item's active status.

        An inactive item will not be validated. Inactive items are
        intended to be used for:

        - future requirements
        - temporarily disabled requirements or tests
        - externally implemented requirements
        - etc.

        """
        return self._data['active']

    @active.setter
    @auto_save
    @auto_load
    def active(self, value):
        """Set the item's active status."""
        self._data['active'] = to_bool(value)

    @property
    @auto_load
    def derived(self):
        """Get the item's derived status.

        A derived item does not have links to items in its parent
        document, but should still be linked to by items in its child
        documents.

        """
        return self._data['derived']

    @derived.setter
    @auto_save
    @auto_load
    def derived(self, value):
        """Set the item's derived status."""
        self._data['derived'] = to_bool(value)

    @property
    @auto_load
    def normative(self):
        """Get the item's normative status.

        A non-normative item should not have or be linked to.
        Non-normative items are intended to be used for:

        - headings
        - comments
        - etc.

        """
        return self._data['normative']

    @normative.setter
    @auto_save
    @auto_load
    def normative(self, value):
        """Set the item's normative status."""
        self._data['normative'] = to_bool(value)

    @property
    def heading(self):
        """Indicate if the item is a heading.

        Headings have a level that ends in zero and are non-normative.

        """
        return self.level.heading and not self.normative

    @heading.setter
    @auto_save
    @auto_load
    def heading(self, value):
        """Set the item's heading status."""
        heading = to_bool(value)
        if heading and not self.heading:
            self.level.heading = True
            self.normative = False
        elif not heading and self.heading:
            self.level.heading = False
            self.normative = True

    @property
    @auto_load
    def cleared(self):
        """Indicate if no links are suspect."""
        items = self.parent_items
        for uid in self.links:
            for item in items:
                if uid == item.uid:
                    if uid.stamp != item.stamp():
                        return False
        return True


# mabe setter and getter for reference here after implemeting clearRef function
        

    @cleared.setter
    @auto_save
    @auto_load
    def cleared(self, value):
        """Set the item's suspect link status."""
        self.clear(_inverse=not to_bool(value))

    @property
    @auto_load
    def reviewed(self):
        """Indicate if the item has been reviewed."""
        stamp = self.stamp(links=True)
 
        if self._data['reviewed'] == Stamp(True):
            self._data['reviewed'] = stamp
        # if self.uid == "yrd-scorpos-002":
            # print(stamp)
        return self._data['reviewed'] == stamp

    @reviewed.setter
    @auto_save
    @auto_load
    def reviewed(self, value):
        """Set the item's review status."""
        self._data['reviewed'] = Stamp(value)

    @property
    @auto_load
    def text(self):
        """Get the item's text."""
        return self._data['text']

    @text.setter
    @auto_save
    @auto_load
    def text(self, value):
        """Set the item's text."""
        self._data['text'] = Text(value)


                                        # add 02.12.2019

    @property
    @auto_load
    def SPEC_RATIONALE(self):
        """Get the item's SPEC_RATIONALE."""
        return self._data['SPEC_RATIONALE']

    @SPEC_RATIONALE.setter
    @auto_save
    @auto_load
    def SPEC_RATIONALE(self, value):
        """Set the item's SPEC_RATIONALE."""
        self._data['SPEC_RATIONALE'] = Text(value)





    @property
    @auto_load
    def SPEC_SHORT_DECRIPTION(self):
        """Get the item's SPEC_SHORT_DECRIPTION."""
        return self._data['SPEC_SHORT_DECRIPTION']

    @SPEC_SHORT_DECRIPTION.setter
    @auto_save
    @auto_load
    def SPEC_SHORT_DECRIPTION(self, value):
        """Set the item's SPEC_SHORT_DECRIPTION."""
        self._data['SPEC_SHORT_DECRIPTION'] = Text(value)





    @property
    @auto_load
    def SPEC_ID(self):
        """Get the item's SPEC_ID."""
        return self._data['SPEC_ID']

    @SPEC_ID.setter
    @auto_save
    @auto_load
    def SPEC_ID(self, value):
        """Set the item's SPEC_ID."""
        self._data['SPEC_ID'] = Text(value)





    @property
    @auto_load
    def SPEC_VERSION(self):
        """Get the item's SPEC_VERSION."""
        return self._data['SPEC_VERSION']

    @SPEC_VERSION.setter
    @auto_save
    @auto_load
    def SPEC_VERSION(self, value):
        """Set the item's SPEC_VERSION."""
        self._data['SPEC_VERSION'] = value





    @property
    @auto_load
    def Assumption(self):
        """Get the item's Assumption."""
        return self._data['Assumption']

    @Assumption.setter
    @auto_save
    @auto_load
    def Assumption(self, value):
        """Set the item's Assumption."""
        self._data['Assumption'] = Text(value)





    @property
    @auto_load
    def Add_Info(self):
        """Get the item's Add_Info."""
        return self._data['Add_Info']

    @Add_Info.setter
    @auto_save
    @auto_load
    def Add_Info(self, value):
        """Set the item's Add_Info."""
        self._data['Add_Info'] = Text(value)




    @property
    @auto_load
    def Author(self):
        """Get the item's Author."""
        return self._data['Author']

    @Author.setter
    @auto_save
    @auto_load
    def Author(self, value):
        """Set the item's Author."""
        self._data['Author'] = Text(value)




    @property
    @auto_load
    def Generation(self):
        """Get the item's Generation."""
        return self._data['Generation']

    @Generation.setter
    @auto_save
    @auto_load
    def Generation(self, value):
        """Set the item's Generation."""
        self._data['Generation'] = Text(value)





    @property
    @auto_load
    def REFINE(self):
        """Get the item's REFINE."""
        return self._data['REFINE']

    @REFINE.setter
    @auto_save
    @auto_load
    def REFINE(self, value):
        """Set the item's REFINE."""
        self._data['REFINE'] = Text(value)




    @property
    @auto_load
    def ASSOCIATED(self):
        """Get the item's ASSOCIATED."""
        return self._data['ASSOCIATED']

    @ASSOCIATED.setter
    @auto_save
    @auto_load
    def ASSOCIATED(self, value):
        """Set the item's ASSOCIATED."""
        self._data['ASSOCIATED'] = Text(value)




    @property
    @auto_load
    def SPEC_STATUS(self):
        """Get the item's SPEC_STATUS."""
        return self._data['SPEC_STATUS']

    @SPEC_STATUS.setter
    @auto_save
    @auto_load
    def SPEC_STATUS(self, value):
        """Set the item's SPEC_STATUS."""
        self._data['SPEC_STATUS'] = Text(value)





    @property
    @auto_load
    def Validation_Ref(self):
        """Get the item's Validation_Ref."""
        return self._data['Validation_Ref']

    @Validation_Ref.setter
    @auto_save
    @auto_load
    def Validation_Ref(self, value):
        """Set the item's Validation_Ref."""
        self._data['Validation_Ref'] = Text(value)




    @property
    @auto_load
    def Validation_Mean(self):
        """Get the item's Validation_Mean."""
        return self._data['Validation_Mean']

    @Validation_Mean.setter
    @auto_save
    @auto_load
    def Validation_Mean(self, value):
        """Set the item's Validation_Mean."""
        self._data['Validation_Mean'] = Text(value)




    @property
    @auto_load
    def Verification_Ref(self):
        """Get the item's Verification_Ref."""
        return self._data['Verification_Ref']

    @Verification_Ref.setter
    @auto_save
    @auto_load
    def Verification_Ref(self, value):
        """Set the item's Verification_Ref."""
        self._data['Verification_Ref'] = Text(value)




    @property
    @auto_load
    def Verification_Mean(self):
        """Get the item's Verification_Mean."""
        return self._data['Verification_Mean']

    @Verification_Mean.setter
    @auto_save
    @auto_load
    def Verification_Mean(self, value):
        """Set the item's Verification_Mean."""
        self._data['Verification_Mean'] = Text(value)





    @property
    @auto_load
    def Verification_Rationale(self):
        """Get the item's Verification_Rationale."""
        return self._data['Verification_Rationale']

    @Verification_Rationale.setter
    @auto_save
    @auto_load
    def Verification_Rationale(self, value):
        """Set the item's Verification_Rationale."""
        self._data['Verification_Rationale'] = Text(value)





    @property
    @auto_load
    def Verification_Status(self):
        """Get the item's Verification_Status."""
        return self._data['Verification_Status']

    @Verification_Status.setter
    @auto_save
    @auto_load
    def Verification_Status(self, value):
        """Set the item's Verification_Status."""
        self._data['Verification_Status'] = Text(value)





    @property
    @auto_load
    def VoV_Ref(self):
        """Get the item's VoV_Ref."""
        return self._data['VoV_Ref']

    @VoV_Ref.setter
    @auto_save
    @auto_load
    def VoV_Ref(self, value):
        """Set the item's VoV_Ref."""
        self._data['VoV_Ref'] = Text(value)





    @property
    @auto_load
    def Allocation(self):
        """Get the item's Allocation."""
        return self._data['Allocation']

    @Allocation.setter
    @auto_save
    @auto_load
    def Allocation(self, value):
        """Set the item's Allocation."""
        self._data['Allocation'] = Text(value)




    @property
    @auto_load
    def SPEC_STATUS(self):
        """Get the item's SPEC_STATUS."""
        return self._data['SPEC_STATUS']

    @SPEC_STATUS.setter
    @auto_save
    @auto_load
    def SPEC_STATUS(self, value):
        """Set the item's SPEC_STATUS."""
        self._data['SPEC_STATUS'] = Text(value)


            	                            # end add

    # Is_Req add 09.01.2020

    @property
    @auto_load
    def Is_Req(self):
        """Get the items Is_Req boolean."""
        return self._data['Is_Req']

    @Is_Req.setter
    @auto_save
    @auto_load
    def Is_Req(self, value):
        """Set the item's Is_Req boolean."""
        self._data['Is_Req'] = to_bool(value)

    # end Is_Req add

    # add 16.01.2020
    # Es werden die attribute hinzugefügt die nur erscheinen wenn es sich nicht um ein Requirment handelt

    @property
    @auto_load
    def EXTENSION(self):
        """Get the items EXTENSION string."""
        return self._NO_REQ_data['EXTENSION']

    @EXTENSION.setter
    @auto_save
    @auto_load
    def EXTENSION(self, value):
        """Set the item's EXTENSION value."""
        self._NO_REQ_data['EXTENSION'] = Text(value)



    @property
    @auto_load
    def TITLE(self):
        """Get the items TITLE string."""
        return self._NO_REQ_data['TITLE']

    @TITLE.setter
    @auto_save
    @auto_load
    def TITLE(self, value):
        """Set the item's TITLE value."""
        self._NO_REQ_data['TITLE'] = Text(value)



    @property
    @auto_load
    def SIDEBAR(self):
        """Get the items SIDEBAR string."""
        return self._NO_REQ_data['SIDEBAR']

    @SIDEBAR.setter
    @auto_save
    @auto_load
    def SIDEBAR(self, value):
        """Set the item's SIDEBAR value."""
        self._NO_REQ_data['SIDEBAR'] = Text(value)
   

# add 10.12.2019
    @property
    @auto_load
    def ref(self):
        """Get the item's external file reference.

        An external reference can be part of a line in a text file or
        the filename of any type of file.

        """
        return sorted(self._data['ref'])

    @ref.setter
    @auto_save
    @auto_load
    def ref(self, value):
        """Set the item's external file reference."""
        self._data['ref'] = set(REF(v) for v in value)

# end add 

    @property
    @auto_load
    def links(self):
        """Get a list of the item UIDs this item links to."""
        return sorted(self._data['links'])

    @links.setter
    @auto_save
    @auto_load
    def links(self, value):
        """Set the list of item UIDs this item links to."""
        self._data['links'] = set(UID(v) for v in value)

    @property
    def parent_links(self):
        """Get a list of the item UIDs this item links to."""
        return self.links  # alias

    @parent_links.setter
    def parent_links(self, value):
        """Set the list of item UIDs this item links to."""
        self.links = value  # alias

    @property
    @requires_tree
    def parent_items(self):
        """Get a list of items that this item links to."""
        items = []
        for uid in self.links:
            try:
                item = self.tree.find_item(uid)
            except DoorstopError:
                item = UnknownItem(uid)
                log.warning(item.exception)
            items.append(item)
        return items

    @property
    @requires_tree
    @requires_document
    def parent_documents(self):
        """Get a list of documents that this item's document should link to.

        .. note::

           A document only has one parent.

        """
        try:
            return [self.tree.find_document(self.document.prefix)]
        except DoorstopError:
            log.warning(Prefix.UNKNOWN_MESSGE.format(self.document.prefix))
            return []

    # actions ################################################################

    @auto_save
    def edit(self, tool=None):
        """Open the item for editing.

        :param tool: path of alternate editor

        """
        # Lock the item
        if self.tree:
            self.tree.vcs.lock(self.path)
        # Open in an editor
        editor.edit(self.path, tool=tool)
        # Force reloaded
        self._loaded = False

    @auto_save
    @auto_load
    def link(self, value):
        """Add a new link to another item UID.

        :param value: item or UID

        """
        uid = UID(value)
        log.info("linking to '{}'...".format(uid))
        self._data['links'].add(uid)
    
    # add 13.12.2019
    @auto_save
    @auto_load
    def add_ref(self,value):
        """Add new reference to Item
        :param value: item or UID
 
        """
        ref = REF(value)
        log.info("referencing to'{}'...".format(ref))
        self._data['ref'].add(ref)

    # end add 



    @auto_save
    @auto_load
    def unlink(self, value):
        """Remove an existing link by item UID.

        :param value: item or UID

        """
        uid = UID(value)
        try:
            self._data['links'].remove(uid)
        except KeyError:
            log.warning("link to {0} does not exist".format(uid))

    def get_issues(self, **kwargs):
        """Yield all the item's issues.

        :return: generator of :class:`~doorstop.common.DoorstopError`,
                              :class:`~doorstop.common.DoorstopWarning`,
                              :class:`~doorstop.common.DoorstopInfo`

        """


        assert kwargs.get('document_hook') is None
        assert kwargs.get('item_hook') is None
        log.info("checking item {}...".format(self))
        # Verify the file can be parsed
        self.load()
       
        # add 09.01.2020 -> If item is not a requirement do nothing
        if self._data['Is_Req'] == False:
            self.save()
            if not self.text:
                yield DoorstopWarning("no text")
            return
        # Skip inactive items
        if not self.active:
            log.info("skipped inactive item: {}".format(self))
            return
        # Delay item save if reformatting
        if settings.REFORMAT:
            self.auto = False
        # Check text
        if not self.text:
            yield DoorstopWarning("no text")
        # Check external references
        if settings.CHECK_REF:
            try:
                self.find_ref()
            except DoorstopError as exc:
                yield exc
        # Check links
        if not self.normative and self.links:
            yield DoorstopWarning("non-normative, but has links")
        # Check links against the document
        if self.document:
            yield from self._get_issues_document(self.document)
        # Check links against the tree
        if self.tree:
            yield from self._get_issues_tree(self.tree)
        # Check links against both document and tree
        if self.document and self.tree:
            yield from self._get_issues_both(self.document, self.tree)
        # Check review status
        # print('REVIEWD:')
        # print(self.reviewed)
        if not self.reviewed:
            if settings.CHECK_REVIEW_STATUS:
                # print('HALLO')
                yield DoorstopWarning("unreviewed changes")
        # Reformat the file
        if settings.REFORMAT:
            log.debug("reformatting item {}...".format(self))
            self.save()

                                                                             # add 13.12.2019

        # check ob references inaktiv gesetzt werden müssen
        for ref in self.ref:
            # falls stamp noch keinen wert hat bekommt er hier den aktuellen
            if ref.stamp != self.stamp(ID=ref.value):
                if settings.CHECK_REF_STATUS:
                    yield DoorstopWarning('suspect reference {}'.format(ref))

        # print(self)
        # print(self.ref)
            

                                                                            # end add

    def _get_issues_document(self, document):
        """Yield all the item's issues against its document."""
        log.debug("getting issues against document...")
        # Verify an item's UID matches its document's prefix
        if self.prefix != document.prefix:
            msg = "prefix differs from document ({})".format(document.prefix)
            yield DoorstopInfo(msg)
        # Verify an item has upward links
        if all((document.parent,
                self.normative,
                not self.derived)) and not self.links:
            msg = "no links to parent document: {}".format(document.parent)
            yield DoorstopWarning(msg)
        # Verify an item's links are to the correct parent
        for uid in self.links:
            try:
                prefix = uid.prefix
            except DoorstopError:
                msg = "invalid UID in links: {}".format(uid)
                yield DoorstopError(msg)
            else:
                if document.parent and prefix != document.parent:
                    # this is only 'info' because a document is allowed
                    # to contain items with a different prefix, but
                    # Doorstop will not create items like this
                    msg = "parent is '{}', but linked to: {}".format(
                        document.parent, uid)
                    yield DoorstopInfo(msg)

    def _get_issues_tree(self, tree):
        """Yield all the item's issues against its tree."""
        log.debug("getting issues against tree...")
        # Verify an item's links are valid
    
        identifiers = set()
        for uid in self.links:
            try:
                item = tree.find_item(uid)
            except DoorstopError:
                identifiers.add(uid)  # keep the invalid UID
                msg = "linked to unknown item: {}".format(uid)
                yield DoorstopError(msg)
            else:
                # check the linked item
                if not item.active:
                    msg = "linked to inactive item: {}".format(item)
                    yield DoorstopInfo(msg)
                if not item.normative:
                    msg = "linked to non-normative item: {}".format(item)
                    yield DoorstopWarning(msg)
                # check the link status
                
                # wenn bis es bis jetzt noch keinen stamp gibt ... funktioniert allerdings glaube ich nicht ....
                if uid.stamp == Stamp(True):
                    uid.stamp = item.stamp()  #... convert True to a stamp
                

                elif uid.stamp != item.stamp():
                    # 12.12.2019
                    # print('STAMPS FOR LINKS')
                    # print(item.stamp())
                    # print(uid.stamp)
                    # print(uid)
                    if settings.CHECK_SUSPECT_LINKS:
                        msg = "suspect link: {}".format(item)
                        yield DoorstopWarning(msg)
                # reformat the item's UID
                identifier2 = UID(item.uid, stamp=uid.stamp)
                identifiers.add(identifier2)
        # Apply the reformatted item UIDs
        if settings.REFORMAT:
            self._data['links'] = identifiers

    def _get_issues_both(self, document, tree):
        """Yield all the item's issues against its document and tree."""
        log.debug("getting issues against document and tree...")
        # Verify an item is being linked to (child links)
        if settings.CHECK_CHILD_LINKS and self.normative:
            items, documents = self._find_child_objects(document=document,
                                                        tree=tree,
                                                        find_all=False)
            if not items:
                for document in documents:
                    msg = "no links from child document: {}".format(document)
                    yield DoorstopWarning(msg)



# add 11.12.2019 umbau in einen for loop 

    @requires_tree
    def find_ref(self, paths=False):
        """Get the external file reference and line number.

        :raises: :class:`~doorstop.common.DoorstopError` when no
            reference is found

        :return: relative path to file or None (when no reference
            set),
            line number (when found in file) or None (when found as
            filename) or None (when no reference set)

        """
                                                        # add 06.01.2020
        # Choose generator to iterate over:
        if paths:
            iterator = paths
        else:
            iterator = self.tree.vcs.paths
                                                         # end add 
        # Return immediately if no external reference
        if not self.ref:
            log.debug("no external reference to search for")
            return None, None
        # Update the cache
        if not settings.CACHE_PATHS:
            pyficache.clear_file_cache()
        # Search for the external reference
        # initialiseren zweier listen die mit den referencen gefüllt werden
        ref_found = {}

        ### hier umbau in loop // self.ref wird überall mit ref.value ersetzt um zugriff auf die einzelnen Strings zu haben !
        for ref in self.ref:
           
            # hinzufügen eines dictionaries mit true == gefunden und false == nicht gefunden -> tracking der gefundenen referencen im code 
            ref_found[ref.value] = False
            

            log.debug("seraching for ref '{}'...".format(ref.value))
            pattern = r"(\b|\W){}(\b|\W)".format(re.escape(ref.value))
            log.trace("regex: {}".format(pattern))
            regex = re.compile(pattern)
            for path, filename, relpath in iterator:
                # Skip the item's file while searching              
                if path == self.path:
                    # pfad zur yaml datei in der referencen stehen ...
                    continue
                # Check for a matching filename
                if filename == ref.value:
                    return relpath, 'Directory'
                # Skip extensions that should not be considered text
                if os.path.splitext(filename)[-1] in settings.SKIP_EXTS:
                    continue
                # Search for the reference in the file
                                                                    # add 11.12.2019 // fill lists added before // 16.12.2019 --> dictionary mit false als value 
                                                                    # wenn nicht gefunden ansonsten tuple mit file/line 
                lines = pyficache.getlines(path)
                if lines is None:
                    log.trace("unable to read lines from: {}".format(path))
                    continue
                
                for lineno, line in enumerate(lines, start=1):
                    if regex.search(line):
                        log.debug("found ref: {}".format(relpath))
                        if ref_found[ref.value] == False:
                            ref_found[ref.value] = (relpath, lineno)
                        else:
                            msg = f"found aaaa multiple times same refernce in code!\n=>('{relpath}', {lineno}) and {ref_found[ref.value]}"
                            raise DoorstopError(msg)

        if ref_found:
            return ref_found
        else: 
           return None
                                                                    # end add 


# end add






    def find_child_links(self, find_all=True):
        """Get a list of item UIDs that link to this item (reverse links).

        :param find_all: find all items (not just the first) before returning

        :return: list of found item UIDs

        """
        items, _ = self._find_child_objects(find_all=find_all)
        identifiers = [item.uid for item in items]
        return identifiers

    child_links = property(find_child_links)

    def find_child_items(self, find_all=True):
        """Get a list of items that link to this item.

        :param find_all: find all items (not just the first) before returning

        :return: list of found items

        """
        items, _ = self._find_child_objects(find_all=find_all)
        return items

    child_items = property(find_child_items)

    def find_child_documents(self):
        """Get a list of documents that should link to this item's document.

        :return: list of found documents

        """
        _, documents = self._find_child_objects(find_all=False)
        return documents

    child_documents = property(find_child_documents)

    def _find_child_objects(self, document=None, tree=None, find_all=True):
        """Get lists of child items and child documents.

        :param document: document containing the current item
        :param tree: tree containing the current item
        :param find_all: find all items (not just the first) before returning

        :return: list of found items, list of all child documents

        """
        child_items = []
        child_documents = []
        document = document or self.document
        tree = tree or self.tree
        if not document or not tree:
            return child_items, child_documents
        # Find child objects
        log.debug("finding item {}'s child objects...".format(self))
        for document2 in tree:
            if document2.parent == document.prefix:
                child_documents.append(document2)
                # Search for child items unless we only need to find one
                if not child_items or find_all:
                    for item2 in document2:
                        if self.uid in item2.links:
                            child_items.append(item2)
                            if not find_all:
                                break
        # Display found links
        if child_items:
            if find_all:
                joined = ', '.join(str(i) for i in child_items)
                msg = "child items: {}".format(joined)
            else:
                msg = "first child item: {}".format(child_items[0])
            log.debug(msg)
            joined = ', '.join(str(d) for d in child_documents)
            log.debug("child documents: {}".format(joined))
        return sorted(child_items), child_documents

    @auto_load
    def stamp(self, links=False, ID=False):
        """Hash the item's key content for later comparison."""
        # add 15.12.2019 values werden nach ID Parameter ausgewählt
        if not ID:
            values = [self.uid, self.text, self.Assumption] #self.ref] reference nicht mit reinnhemen weil sie siich verändert bei clear ref 
                                            # un damit das säubern reihenfolgenahbhängig wird


            if links:
                values.extend(self.links)
             
            

        else:

        # end add 
            values = [self.text,self.Assumption, ID]
            # print(f'VALUES:{values}')
            
        return Stamp(*values)

    @auto_save
    @auto_load
    def clear(self, _inverse=False):
        """Clear suspect links."""
        log.info("clearing suspect links...")
        items = self.parent_items
        for uid in self.links:
            for item in items:
                if uid == item.uid:
                    if _inverse:
                        uid.stamp = Stamp()
                    else:
                        uid.stamp = item.stamp()


    @auto_save
    @auto_load
    def review(self):
        """Mark the item as reviewed."""
        log.info("marking item as reviewed...")
        self._data['reviewed'] = self.stamp(links=True)
       


        # add 15.12.2019
    @auto_save
    @auto_load
    def clearRef(self, referenceID):
        """change suspect refernece status"""
        log.info("marking reference as reviewed...")
        # Mit found_id wird sichergestellt, dass auch eine ID gefunden wurd
        # ansonsten wir fehler ausgegen das die angegebne ID nicht gefunden werdne kann.. 
        found_id = False 
        if referenceID == 'all':
            found_id = True
            for ref in self.ref:
                # item aktuellen stamp aus spezifischer id und text geben
                ref.stamp = self.stamp(ID=ref.value)

        else:
             for ref in self.ref:
                 if referenceID == ref.value:
                    found_id = True
                    ref.stamp = self.stamp(ID=ref.value)

        if not found_id:
            raise DoorstopError("ID does not exist: {}".format(referenceID))

           
    # end add

    @delete_item
    def delete(self, path=None):
        """Delete the item."""
        pass  # the item is deleted in the decorated method



class UnknownItem(object):

    """Represents an unknown item, which doesn't have a path."""

    UNKNOWN_PATH = '???'  # string to represent an unknown path

    normative = False  # do not include unknown items in traceability

    def __init__(self, value, spec=Item):
        self._uid = UID(value)
        self._spec = dir(spec)  # list of attribute names for warnings
        msg = UID.UNKNOWN_MESSAGE.format(k='', u=self.uid)
        self.exception = DoorstopError(msg)

    def __str__(self):
        return Item.__str__(self)

    def __getattr__(self, name):
        if name in self._spec:
            log.debug(self.exception)
        return self.__getattribute__(name)

    @property
    def uid(self):
        """Get the item's UID."""
        return self._uid

    prefix = Item.prefix
    number = Item.number

    @property
    def relpath(self):
        """Get the unknown item's relative path string."""
        return "@{}???".format(os.sep, self.UNKNOWN_PATH)

    def stamp(self):  # pylint: disable=R0201
        """Return an empty stamp."""
        return Stamp(None)
