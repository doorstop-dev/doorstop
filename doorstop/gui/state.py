#!/usr/bin/env python

from typing import FrozenSet
from typing import Optional
from typing import Tuple

import os

from doorstop.core.tree import Tree
from doorstop.core.types import Prefix
from doorstop.core.types import UID


class State(object):

    @property
    def cwd(self) -> str:
        return self.__cwd

    @cwd.setter
    def cwd(self, value: Optional[str]) -> None:
        self.__cwd = os.getcwd() if value is None else value

    @property
    def project_path(self) -> str:
        return self.__project_path

    @project_path.setter
    def project_path(self, value: Optional[str]) -> None:
        self.__project_path = "" if value is None else str(value)

    @property
    def project_tree(self) -> Optional[Tree]:
        return self.__project_tree

    @project_tree.setter
    def project_tree(self, value: Optional[Tree]) -> None:
        self.__project_tree = value

    @property
    def session_pending_change(self) -> bool:
        return self.__session_pending_change

    @session_pending_change.setter
    def session_pending_change(self, value: Optional[bool]) -> None:
        self.__session_pending_change = bool(value)

    @property
    def session_selected_document(self) -> Prefix:
        result = self.__session_selected_document
        if result: return result

        project_tree = self.project_tree
        for curr_document in [] if project_tree is None else project_tree:
            # Select the first one
            return curr_document.prefix
        return self.__session_selected_document

    @session_selected_document.setter
    def session_selected_document(self, value: Prefix) -> None:
        self.__session_selected_document = value

    @property
    def session_selected_item(self) -> Tuple[UID, ...]:
        result = self.__session_selected_item
        if result: return result

        project_tree = self.project_tree
        for item in [] if project_tree is None else project_tree.find_document(self.session_selected_document).items:
            # Select the first one
            return (item.uid, )
        return ()

    @session_selected_item.setter
    def session_selected_item(self, value: Optional[Tuple[UID, ...]]) -> None:
        self.__session_selected_item = tuple() if value is None else value

    @property
    def session_selected_item_principal(self) -> Optional[UID]:
        try:
            return self.session_selected_item[0]
        except IndexError:
            return None

    @property
    def session_link_inception(self) -> str:
        return self.__session_link_inception

    @session_link_inception.setter
    def session_link_inception(self, value: Optional[str]) -> None:
        self.__session_link_inception = "" if value is None else value

    @property
    def session_selected_link(self) -> FrozenSet[UID]:
        return self.__session_selected_link

    @session_selected_link.setter
    def session_selected_link(self, value: Optional[FrozenSet[UID]]) -> None:
        self.__session_selected_link = frozenset() if value is None else value

    @property
    def session_extended_name(self) -> str:
        return self.__session_extended_name

    @session_extended_name.setter
    def session_extended_name(self, value: Optional[str]) -> None:
        self.__session_extended_name = "" if value is None else value

    def __init__(self) -> None:
        self.cwd = None
        self.project_path = None
        self.project_tree = None
        self.session_pending_change = None
        self.session_selected_document = None
        self.session_selected_item = None
        self.session_link_inception = None
        self.session_selected_link = None
        self.session_extended_name = None
