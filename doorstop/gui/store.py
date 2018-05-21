#!/usr/bin/env python

from typing import Optional
from typing import Callable

from doorstop.gui.action import Action
from doorstop.gui.state import State
from doorstop.gui.reducer import Reducer


class Store(object):

    @property
    def state(self) -> Optional[State]:
        return self.__state

    def __init__(self, reducer: Reducer, initial_state: Optional[State] = None) -> None:
        self.__observer = []
        self.__state = initial_state
        self.__reducer = reducer

    def add_observer(self, observer: Callable[["Store"], None]):
        self.__observer.append(observer)
        observer(self)

    def remove_observer(self, observer: Callable[["Store"], None]):
        self.__observer.remove(observer)

    def dispatch(self, action: Action) -> None:
        new_state = self.__reducer.reduce(self.state, action)
        if new_state != self.__state:
            print(action.__class__.__name__)
            self.__state = new_state
            for curr_observer in self.__observer:
                curr_observer(self)
        else:
            print()
