#!/usr/bin/env python

import copy
import os

from typing import Generator
from typing import Set

from doorstop.gui.action import Action
from doorstop.gui.action import Action_ChangeCWD
from doorstop.gui.action import Action_ChangeProjectPath
from doorstop.gui.action import Action_CloseProject
from doorstop.gui.action import Action_LoadProject
from doorstop.gui.action import Action_SaveProject
from doorstop.gui.action import Action_ChangeSelectedDocument
from doorstop.gui.action import Action_ChangeSelectedItem
from doorstop.gui.action import Action_ChangeItemText
from doorstop.gui.action import Action_ChangeItemReference
from doorstop.gui.action import Action_ChangeItemActive
from doorstop.gui.action import Action_ChangeItemDerived
from doorstop.gui.action import Action_ChangeItemNormative
from doorstop.gui.action import Action_ChangeItemHeading
from doorstop.gui.action import Action_ChangeSelectedLink
from doorstop.gui.action import Action_ChangeLinkInception
from doorstop.gui.action import Action_ChangeItemAddLink
from doorstop.gui.action import Action_ChangeItemRemoveLink
from doorstop.gui.action import Action_ChangeExtendedName
from doorstop.gui.action import Action_ChangeExtendedValue
from doorstop.gui.action import Action_AddNewItemNextToSelection
from doorstop.gui.action import Action_RemoveSelectedItem
from doorstop.gui.action import Action_SelectedItem_Level_Indent
from doorstop.gui.action import Action_SelectedItem_Level_Dedent
from doorstop.gui.action import Action_SelectedItem_Level_Increment
from doorstop.gui.action import Action_SelectedItem_Level_Decrement
from doorstop.gui.action import Action_Import

from doorstop.gui.state import State

from doorstop.core.types import UID

from doorstop.core import builder
from doorstop.core import importer

from doorstop.core.document import Document
from doorstop.core.item import Item

from doorstop.common import DoorstopError


class Reducer(object):
    def __init__(self) -> None:
        pass

    def reduce(self, state: State, action: Action) -> State:
        return state


class Reducer_CWD(Reducer):
    def reduce(self, state: State, action: Action) -> State:
        result = state
        if isinstance(action, Action_ChangeCWD):
            newCWD = os.getcwd() if action.cwd is None else action.cwd
            if newCWD != result.cwd:
                result = copy.deepcopy(result)
                result.cwd = newCWD
        return result


class Reducer_Project(Reducer):
    def reduce(self, state: State, action: Action) -> State:
        result = state
        new_path = state.project_path
        new_tree = state.project_tree
        if isinstance(action, Action_ChangeProjectPath):
            new_path = action.project_path
            new_tree = None
        elif isinstance(action, Action_LoadProject):
            new_tree = None
        elif isinstance(action, Action_CloseProject):
            new_path = ""
            new_tree = None
        elif isinstance(action, Action_SaveProject):
            project_tree = state.project_tree
            if project_tree is not None:
                for c_curr_document in project_tree:
                    c_curr_document.save()
                    for c_curr_item in c_curr_document:
                        c_curr_item.save()
                    if state.session_pending_change:
                        result = copy.deepcopy(result)
                        result.session_pending_change = False

        if (new_path != result.project_path) or (new_tree != result.project_tree):
            result = copy.deepcopy(result)
            result.session_selected_item = None
            result.session_selected_link = None
            result.project_tree = None if "" == new_path else builder.build(cwd=state.cwd, root=new_path, is_auto_save=False)
            if result.project_tree is not None:
                new_path = result.project_tree.root
            result.project_path = new_path
        return result


class Reducer_Session(Reducer):
    def reduce(self, state: State, action: Action) -> State:
        result = state
        if isinstance(action, Action_ChangeSelectedDocument):
            new_selected_document = action.selected_document
            if new_selected_document != state.session_selected_document:
                result = copy.deepcopy(result)
                result.session_selected_document = new_selected_document
                result.session_selected_item = None
        elif isinstance(action, Action_ChangeSelectedItem):
            new_selected_item = action.selected_item
            if set(str(a) for a in new_selected_item) != set(str(b) for b in state.session_selected_item):
                result = copy.deepcopy(result)

                # Load in the state the selection by putting the freshly selecte item first so that the main selected item becomes one of the freshly selected item.
                previous_selection = [str(x) for x in state.session_selected_item]
                freshly_selected = [str(y) for y in new_selected_item if y not in previous_selection]
                unchanged_selection = [str(z) for z in new_selected_item if z in previous_selection]
                freshly_selected.extend(unchanged_selection)
                result.session_selected_item = tuple([UID(aa) for aa in freshly_selected])
        elif isinstance(action, Action_ChangeSelectedLink):
            new_selected_link = frozenset(set([x for x in result.session_selected_link]).union(action.selected_link) - action.unselected_link)
            if new_selected_link != result.session_selected_link:
                result = copy.deepcopy(result)
                result.session_selected_link = new_selected_link
        elif isinstance(action, Action_ChangeLinkInception):
            new_inception_link = action.inception_link
            if new_inception_link != result.session_link_inception:
                result = copy.deepcopy(result)
                result.session_link_inception = new_inception_link
        elif isinstance(action, Action_ChangeExtendedName):
            new_extended_name = action.extendedName
            if new_extended_name != result.session_extended_name:
                result = copy.deepcopy(result)
                result.session_extended_name = new_extended_name
        return result


class Reducer_Edit(Reducer):
    def reduce(self, state: State, action: Action) -> State:
        result = state
        if isinstance(action, Action_ChangeItemText):
            project_tree = state.project_tree
            old_item = project_tree.find_item(action.item_uid) if project_tree else None

            if old_item:
                old_item_text = old_item.text
                new_item_text = action.item_new_text
                if old_item_text != new_item_text:
                    result = copy.deepcopy(result)
                    project_tree = result.project_tree
                    if project_tree:
                        new_item = project_tree.find_item(action.item_uid)
                        new_item.text = new_item_text
                        result.session_pending_change = True
        if isinstance(action, Action_ChangeItemReference):
            project_tree = state.project_tree
            old_item = project_tree.find_item(action.item_uid) if project_tree else None

            if old_item:
                old_item_reference = old_item.ref
                new_item_reference = action.item_new_reference
                if old_item_reference != new_item_reference:
                    result = copy.deepcopy(result)
                    project_tree = result.project_tree
                    if project_tree:
                        new_item = project_tree.find_item(action.item_uid)
                        new_item.ref = new_item_reference
                        result.session_pending_change = True
        elif isinstance(action, Action_ChangeItemActive):
            project_tree = state.project_tree
            old_item = project_tree.find_item(action.item_uid) if project_tree else None

            if old_item:
                old_item_active = old_item.active
                new_item_active = action.item_new_active
                if old_item_active != new_item_active:
                    result = copy.deepcopy(result)
                    project_tree = result.project_tree
                    if project_tree:
                        new_item = project_tree.find_item(action.item_uid)
                        new_item.active = new_item_active
                        result.session_pending_change = True
        elif isinstance(action, Action_ChangeItemDerived):
            project_tree = state.project_tree
            old_item = project_tree.find_item(action.item_uid) if project_tree else None

            if old_item:
                old_item_derived = old_item.derived
                new_item_derived = action.item_new_derived
                if old_item_derived != new_item_derived:
                    result = copy.deepcopy(result)
                    project_tree = result.project_tree
                    if project_tree:
                        new_item = project_tree.find_item(action.item_uid)
                        new_item.derived = new_item_derived
                        result.session_pending_change = True
        elif isinstance(action, Action_ChangeItemNormative):
            project_tree = state.project_tree
            old_item = project_tree.find_item(action.item_uid) if project_tree else None

            if old_item:
                old_item_normative = old_item.normative
                new_item_normative = action.item_new_normative
                if old_item_normative != new_item_normative:
                    result = copy.deepcopy(result)
                    project_tree = result.project_tree
                    if project_tree:
                        new_item = project_tree.find_item(action.item_uid)
                        new_item.normative = new_item_normative
                        result.session_pending_change = True
        elif isinstance(action, Action_ChangeItemHeading):
            project_tree = state.project_tree
            old_item = project_tree.find_item(action.item_uid) if project_tree else None

            if old_item:
                old_item_heading = old_item.heading
                new_item_heading = action.item_new_heading
                if old_item_heading != new_item_heading:
                    result = copy.deepcopy(result)
                    project_tree = result.project_tree
                    if project_tree:
                        new_item = project_tree.find_item(action.item_uid)
                        new_item.heading = new_item_heading
                        result.session_pending_change = True
        elif isinstance(action, Action_ChangeItemRemoveLink):
            project_tree = state.project_tree
            old_item = project_tree.find_item(action.item_uid) if project_tree else None

            if old_item:
                item_link = action.item_link
                result = copy.deepcopy(result)
                project_tree = result.project_tree
                if project_tree:
                    new_item = project_tree.find_item(action.item_uid)
                    count_before = len(new_item.links)
                    new_item.links = [x for x in new_item.links if str(x) not in [str(y) for y in item_link]]
                    result.session_selected_link = frozenset([x for x in result.session_selected_link if str(x) not in [str(y) for y in item_link]])
                    count_after = len(new_item.links)
                    if count_before != count_after:
                        result.session_pending_change = True
        elif isinstance(action, Action_ChangeItemAddLink):
            new_link = action.new_link
            if "" != new_link:

                project_tree = state.project_tree
                old_item = project_tree.find_item(action.item_uid) if project_tree else None

                if old_item:
                    if new_link not in old_item.links:
                        result = copy.deepcopy(result)
                        project_tree = result.project_tree
                        if project_tree:
                            new_item = project_tree.find_item(action.item_uid)
                            links = new_item.links
                            links.append(UID(new_link))
                            new_item.links = links
                            result.session_pending_change = True
        elif isinstance(action, Action_ChangeExtendedValue):
            project_tree = state.project_tree
            old_item = project_tree.find_item(action.item_uid) if project_tree else None
            if old_item:
                old_item_extended_value = old_item.get(action.extendedName)
                new_item_extended_value = action.extendedValue
                if old_item_extended_value != new_item_extended_value:
                    result = copy.deepcopy(result)
                    project_tree = result.project_tree
                    if project_tree:
                        new_item = project_tree.find_item(action.item_uid)
                        if new_item_extended_value and new_item_extended_value.strip():
                            new_item.set(action.extendedName, new_item_extended_value)
                        else:
                            new_item.remove(action.extendedName)
                        result.session_pending_change = True
        elif isinstance(action, Action_AddNewItemNextToSelection):
            project_tree = state.project_tree
            if project_tree is not None:
                result = copy.deepcopy(result)
                project_tree = result.project_tree
                assert project_tree is not None
                session_selected_item_principal = state.session_selected_item_principal
                session_selected_item_principal_item = None if session_selected_item_principal is None else project_tree.find_item(session_selected_item_principal)
                document = project_tree.find_document(result.session_selected_document)
                new_item = document.add_item(level=None if session_selected_item_principal_item is None else session_selected_item_principal_item.level + 1)
                result.session_pending_change = True
                result.session_selected_item = (new_item.uid, )
        elif isinstance(action, Action_RemoveSelectedItem):
            project_tree = state.project_tree
            if (project_tree is not None) and (state.session_selected_item_principal is not None):
                result = copy.deepcopy(result)

                session_selected_item_principal = result.session_selected_item_principal
                assert session_selected_item_principal is not None

                project_tree = result.project_tree
                assert project_tree is not None

                document = project_tree.find_document(result.session_selected_document)
                item_before = None
                item = None
                item_after = None
                found_it = False
                for curr_neighboor in document.items:
                    if found_it:
                        if str(curr_neighboor.uid) not in result.session_selected_item:
                            item_after = curr_neighboor
                            break
                    else:
                        if str(session_selected_item_principal) == str(curr_neighboor.uid):
                            item = curr_neighboor
                            found_it = True
                        else:
                            if str(curr_neighboor.uid) not in result.session_selected_item:
                                item_before = curr_neighboor

                assert item is not None, str(session_selected_item_principal)

                new_selection = None
                if item_before is None:
                    if item_after is None:
                        new_selection = None
                    else:
                        new_selection = [item_after.uid]
                else:
                    if item_after is None:
                        new_selection = [item_before.uid]
                    else:
                        # Use heuristic to chose the best userfriendly new selection.
                        item_before_level = item_before.level.value
                        item_level = item.level.value
                        item_after_level = item_after.level.value

                        for idx, val in enumerate(item_level):
                            if val == item_after_level[idx]:
                                if val == item_before_level[idx]:
                                    continue  # They are both equaly similar
                                else:
                                    # The after looks more similar
                                    new_selection = [item_after.uid]
                                    break
                            else:
                                if val == item_before_level[idx]:
                                    # The before looks more similar
                                    new_selection = [item_before.uid]
                                    break
                                else:
                                    # They are both equaly not similar
                                    new_selection = [item_after.uid]
                                    break

                for c_currUID in result.session_selected_item:
                    item = project_tree.find_item(c_currUID)
                    if item is not None:
                        item = project_tree.remove_item(item)
                        result.session_pending_change |= item is not None
                        result.session_selected_item = new_selection
        elif isinstance(action, Action_Import):
            source = action.file_to_import
            if source:
                project_tree = state.project_tree
                if project_tree is not None:
                    resultX = copy.deepcopy(result)
                    project_tree = resultX.project_tree
                    assert project_tree is not None

                    the_document = None
                    try:
                        the_document = project_tree.find_document(state.session_selected_document)
                    except DoorstopError:
                        pass  # The document is not found.
                    if the_document is not None:
                        ext = source[source.rfind("."):]
                        func = importer.check(ext)
                        if func is not None:
                            func(is_auto_save=False, path=source, document=the_document, mapping=None)
                            result = resultX
                            result.session_pending_change = True

        return result


class Reducer_Level(Reducer):
    def reduce(self, state: State, action: Action) -> State:
        result = state

        def getNextFromStart(document: Document, uid_to_process: Set[str]) -> Generator[Item, None, None]:
            uid_to_process_left = set(uid_to_process)
            while uid_to_process_left:
                the_next_item_to_process = next((x for x in document.items if str(x.uid) in uid_to_process_left), None)  # pylint: disable=R1708
                if the_next_item_to_process is None: return
                yield the_next_item_to_process
                uid_to_process_left.remove(str(the_next_item_to_process.uid))

        def getNextFromEnd(document: Document, uid_to_process: Set[str]) -> Generator[Item, None, None]:
            uid_to_process_left = set(uid_to_process)
            while uid_to_process_left:
                the_next_item_to_process = next((x for x in reversed(document.items) if str(x.uid) in uid_to_process_left), None)  # pylint: disable=R1708
                if the_next_item_to_process is None: return
                yield the_next_item_to_process
                uid_to_process_left.remove(str(the_next_item_to_process.uid))

        if isinstance(action, (Action_SelectedItem_Level_Indent, Action_SelectedItem_Level_Dedent, Action_SelectedItem_Level_Increment, Action_SelectedItem_Level_Decrement)):
            project_tree = state.project_tree
            if (project_tree is not None) and (state.session_selected_item_principal is not None):
                result = copy.deepcopy(result)
                session_selected_item = result.session_selected_item

                project_tree = result.project_tree
                assert project_tree is not None

                document = project_tree.find_document(result.session_selected_document)

                for x in (getNextFromStart if isinstance(action, (Action_SelectedItem_Level_Decrement)) else getNextFromEnd)(document, session_selected_item):
                    result.session_pending_change = True
                    if isinstance(action, Action_SelectedItem_Level_Indent):
                        x.level >>= 1
                        document.reorder(keep=x)
                    elif isinstance(action, Action_SelectedItem_Level_Dedent):
                        x.level <<= 1
                        document.reorder(keep=x)
                    elif isinstance(action, Action_SelectedItem_Level_Increment):
                        x.level += 2
                        document.reorder(keep=x)
                    elif isinstance(action, Action_SelectedItem_Level_Decrement):
                        x.level -= 1
                        document.reorder(keep=x)
        return result


class Reducer_GUI(Reducer):
    def reduce(self, state: State, action: Action) -> State:
        result = state
        for curr_reducer in (Reducer_CWD(), Reducer_Project(), Reducer_Session(), Reducer_Edit(), Reducer_Level()):
            result = curr_reducer.reduce(result, action)
        return result
