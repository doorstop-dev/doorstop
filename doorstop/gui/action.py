#!/usr/bin/env python

from typing import Optional
from typing import Tuple
from typing import FrozenSet

from doorstop.core.types import Prefix
from doorstop.core.types import UID


class Action(object): pass


class Action_ChangeProjectPath(Action):
    @property
    def project_path(self) -> str:
        return self.__project_path

    def __init__(self, project_path: str) -> None:
        self.__project_path = str(project_path) if project_path else ""


class Action_CloseProject(Action): pass


class Action_LoadProject(Action): pass


class Action_SaveProject(Action): pass


class Action_ChangeCWD(Action):
    @property
    def cwd(self) -> Optional[str]:
        return self.__cwd

    def __init__(self, cwd: Optional[str]) -> None:
        self.__cwd = cwd


class Action_ChangeSelectedDocument(Action):
    @property
    def selected_document(self) -> Optional[Prefix]:
        return self.__selected_document

    def __init__(self, selected_document: Optional[Prefix]) -> None:
        self.__selected_document = selected_document


class Action_ChangeSelectedItem(Action):
    @property
    def selected_item(self) -> Tuple[UID, ...]:
        return self.__selected_item

    def __init__(self, selected_item: Tuple[UID, ...]) -> None:
        self.__selected_item = selected_item


class Action_ChangeItemText(Action):
    @property
    def item_uid(self) -> UID:
        return self.__item_uid

    @property
    def item_new_text(self) -> str:
        return self.__item_new_text

    def __init__(self, item_uid: UID, new_text: str) -> None:
        self.__item_uid = item_uid
        self.__item_new_text = new_text


class Action_ChangeItemActive(Action):
    @property
    def item_uid(self) -> UID:
        return self.__item_uid

    @property
    def item_new_active(self) -> bool:
        return self.__item_new_active

    def __init__(self, item_uid: UID, new_active: bool) -> None:
        self.__item_uid = item_uid
        self.__item_new_active = new_active


class Action_ChangeItemDerived(Action):
    @property
    def item_uid(self) -> UID:
        return self.__item_uid

    @property
    def item_new_derived(self) -> bool:
        return self.__item_new_derived

    def __init__(self, item_uid: UID, new_derived: bool) -> None:
        self.__item_uid = item_uid
        self.__item_new_derived = new_derived


class Action_ChangeItemNormative(Action):
    @property
    def item_uid(self) -> UID:
        return self.__item_uid

    @property
    def item_new_normative(self) -> bool:
        return self.__item_new_normative

    def __init__(self, item_uid: UID, new_normative: bool) -> None:
        self.__item_uid = item_uid
        self.__item_new_normative = new_normative


class Action_ChangeItemHeading(Action):
    @property
    def item_uid(self) -> UID:
        return self.__item_uid

    @property
    def item_new_heading(self) -> bool:
        return self.__item_new_heading

    def __init__(self, item_uid: UID, new_heading: bool) -> None:
        self.__item_uid = item_uid
        self.__item_new_heading = new_heading


class Action_ChangeLinkInception(Action):
    @property
    def inception_link(self) -> str:
        return self.__inception_link

    def __init__(self, inception_link: str) -> None:
        self.__inception_link = inception_link


class Action_ChangeItemAddLink(Action):
    @property
    def item_uid(self) -> UID:
        return self.__item_uid

    @property
    def new_link(self) -> UID:
        return self.__new_link

    def __init__(self, item_uid: UID, item_link: UID) -> None:
        self.__item_uid = item_uid
        self.__new_link = item_link


class Action_ChangeSelectedLink(Action):
    @property
    def selected_link(self) -> FrozenSet[UID]:
        return self.__selected_link

    @property
    def unselected_link(self) -> FrozenSet[UID]:
        return self.__unselected_link

    def __init__(self, selected_link: FrozenSet[UID], unselected_link: FrozenSet[UID]) -> None:
        self.__selected_link = selected_link
        self.__unselected_link = unselected_link


class Action_ChangeItemRemoveLink(Action):
    @property
    def item_uid(self) -> UID:
        return self.__item_uid

    @property
    def item_link(self) -> FrozenSet[UID]:
        return self.__item_link

    def __init__(self, item_uid: UID, item_link: FrozenSet[UID]) -> None:
        self.__item_uid = item_uid
        self.__item_link = item_link


class Action_ChangeItemReference(Action):
    @property
    def item_uid(self) -> UID:
        return self.__item_uid

    @property
    def item_new_reference(self) -> str:
        return self.__item_new_reference

    def __init__(self, item_uid: UID, new_reference: str) -> None:
        self.__item_uid = item_uid
        self.__item_new_reference = new_reference


class Action_ChangeExtendedName(Action):
    @property
    def extendedName(self) -> str:
        return self.__extendedName

    def __init__(self, extendedName: Optional[str]) -> None:
        self.__extendedName = "" if extendedName is None else extendedName


class Action_ChangeExtendedValue(Action):
    @property
    def item_uid(self) -> UID:
        return self.__item_uid

    @property
    def extendedName(self) -> str:
        return self.__extendedName

    @property
    def extendedValue(self) -> Optional[str]:
        return self.__extendedValue

    def __init__(self, item_uid: UID, extendedName: str, extendedValue: Optional[str]) -> None:
        self.__item_uid = item_uid
        self.__extendedName = extendedName
        self.__extendedValue = extendedValue
