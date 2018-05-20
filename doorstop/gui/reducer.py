#!/usr/bin/env python

import copy
import os

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


from doorstop.gui.state import State

from doorstop.core.types import UID

from doorstop.core import builder


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
            result.session_selected_item = tuple()
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
            if new_selected_item != state.session_selected_item:
                result = copy.deepcopy(result)
                result.session_selected_item = new_selected_item
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
        return result


class Reducer_GUI(Reducer):
    def reduce(self, state: State, action: Action) -> State:
        result = state
        for curr_reducer in (Reducer_CWD(), Reducer_Project(), Reducer_Session(), Reducer_Edit()):
            result = curr_reducer.reduce(result, action)
        return result
