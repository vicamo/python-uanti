# Copyright 2023 You-Sheng Yang
# Copyright 2013-2019 Gauvain Pocentek, 2019-2022 python-gitlab team

# This file is part of uanti.
#
# uanti is free software: you can redistribute it and/or modify it under the
# terms of the GNU Lesser General Public License as published by the Free
# Software Foundation, version 3 of the License.
#
# uanti is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE. See the GNU Lesser General Public License for more
# details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with uanti. If not, see <http://www.gnu.org/licenses/>.

from typing import (
    Any,
    Callable,
    cast,
    Dict,
    List,
    Optional,
    Tuple,
    Type,
    TypeVar,
    TYPE_CHECKING,
    Union,
)

import argparse
import functools

from uanti.restful.base import RestfulObject, RestfulManager
from uanti.restful.mixins import GetWithoutIdMixin
from uanti.restful.utils import to_dasherized_lowercase


# https://github.com/python/typeshed/issues/7539#issuecomment-1076581049
if TYPE_CHECKING:
    _SubparserType = argparse._SubParsersAction[argparse.ArgumentParser]
else:
    _SubparserType = Any


# custom_actions = {
#    cls: {
#        action: (mandatory_args, optional_args, in_obj),
#    },
# }
custom_actions: Dict[
    str, Dict[str, Tuple[Tuple[str, ...], Tuple[str, ...], bool]]
] = {}


# For an explanation of how these type-hints work see:
# https://mypy.readthedocs.io/en/stable/generics.html#declaring-decorators
#
# The goal here is that functions which get decorated will retain their types.
__F = TypeVar("__F", bound=Callable[..., Any])


def register_custom_action(
    cls_names: Union[str, Tuple[str, ...]],
    mandatory: Tuple[str, ...] = (),
    optional: Tuple[str, ...] = (),
    custom_action: Optional[str] = None,
) -> Callable[[__F], __F]:
    def wrap(f: __F) -> __F:
        @functools.wraps(f)
        def wrapped_f(*args: Any, **kwargs: Any) -> Any:
            return f(*args, **kwargs)

        # in_obj defines whether the method belongs to the obj or the manager
        in_obj = True
        if isinstance(cls_names, tuple):
            classes = cls_names
        else:
            classes = (cls_names,)

        for cls_name in classes:
            final_name = cls_name
            if cls_name.endswith("Manager"):
                final_name = cls_name.replace("Manager", "")
                in_obj = False
            if final_name not in custom_actions:
                custom_actions[final_name] = {}

            action = custom_action or f.__name__.replace("_", "-")
            custom_actions[final_name][action] = (mandatory, optional, in_obj)

        return cast(__F, wrapped_f)

    return wrap


def _populate_sub_parser_by_class(
    obj_cls: Type[RestfulObject],
    mgr_cls: Type[RestfulManager],
    sub_parser: _SubparserType,
) -> None:
    action_parsers: Dict[str, argparse.ArgumentParser] = {}
    for action_name in ["list", "get", "create", "update", "delete"]:
        if not hasattr(mgr_cls, action_name):
            continue

        sub_parser_action = sub_parser.add_parser(
            action_name, conflict_handler="resolve"
        )
        action_parsers[action_name] = sub_parser_action
        sub_parser_action.add_argument("--sudo", required=False)
        if mgr_cls._from_parent_attrs:
            for x in mgr_cls._from_parent_attrs:
                sub_parser_action.add_argument(
                    f"--{x.replace('_', '-')}", required=True
                )

        if action_name == "list":
            for x in mgr_cls._list_filters:
                sub_parser_action.add_argument(
                    f"--{x.replace('_', '-')}", required=False
                )

        if action_name == "delete":
            if obj_cls._id_attr is not None:
                id_attr = obj_cls._id_attr.replace("_", "-")
                sub_parser_action.add_argument(f"--{id_attr}", required=True)

        if action_name == "get":
            if not issubclass(obj_cls, GetWithoutIdMixin):
                if obj_cls._id_attr is not None:
                    id_attr = obj_cls._id_attr.replace("_", "-")
                    sub_parser_action.add_argument(
                        f"--{id_attr}", required=True
                    )

            for x in mgr_cls._optional_get_attrs:
                sub_parser_action.add_argument(
                    f"--{x.replace('_', '-')}", required=False
                )

        if action_name == "create":
            for x in mgr_cls._create_attrs.required:
                sub_parser_action.add_argument(
                    f"--{x.replace('_', '-')}", required=True
                )
            for x in mgr_cls._create_attrs.optional:
                sub_parser_action.add_argument(
                    f"--{x.replace('_', '-')}", required=False
                )

        if action_name == "update":
            if obj_cls._id_attr is not None:
                id_attr = obj_cls._id_attr.replace("_", "-")
                sub_parser_action.add_argument(f"--{id_attr}", required=True)

            for x in mgr_cls._update_attrs.required:
                if x != obj_cls._id_attr:
                    sub_parser_action.add_argument(
                        f"--{x.replace('_', '-')}", required=True
                    )

            for x in mgr_cls._update_attrs.optional:
                if x != obj_cls._id_attr:
                    sub_parser_action.add_argument(
                        f"--{x.replace('_', '-')}", required=False
                    )

    if obj_cls.__name__ in custom_actions:
        name = obj_cls.__name__
        for action_name in custom_actions[name]:
            # NOTE(jlvillal): If we put a function for the `default` value of
            # the `get` it will always get called, which will break things.
            action_parser = action_parsers.get(action_name)
            if action_parser is None:
                sub_parser_action = sub_parser.add_parser(action_name)
            else:
                sub_parser_action = action_parser
            # Get the attributes for URL/path construction
            if mgr_cls._from_parent_attrs:
                for x in mgr_cls._from_parent_attrs:
                    sub_parser_action.add_argument(
                        f"--{x.replace('_', '-')}", required=True
                    )
                sub_parser_action.add_argument("--sudo", required=False)

            # We need to get the object somehow
            if not issubclass(obj_cls, GetWithoutIdMixin):
                if obj_cls._id_attr is not None:
                    id_attr = obj_cls._id_attr.replace("_", "-")
                    sub_parser_action.add_argument(
                        f"--{id_attr}", required=True
                    )

            required, optional, dummy = custom_actions[name][action_name]
            for x in required:
                if x != obj_cls._id_attr:
                    sub_parser_action.add_argument(
                        f"--{x.replace('_', '-')}", required=True
                    )
            for x in optional:
                if x != obj_cls._id_attr:
                    sub_parser_action.add_argument(
                        f"--{x.replace('_', '-')}", required=False
                    )

    if mgr_cls.__name__ in custom_actions:
        name = mgr_cls.__name__
        for action_name in custom_actions[name]:
            # NOTE(jlvillal): If we put a function for the `default` value of
            # the `get` it will always get called, which will break things.
            action_parser = action_parsers.get(action_name)
            if action_parser is None:
                sub_parser_action = sub_parser.add_parser(action_name)
            else:
                sub_parser_action = action_parser
            if mgr_cls._from_parent_attrs:
                for x in mgr_cls._from_parent_attrs:
                    sub_parser_action.add_argument(
                        f"--{x.replace('_', '-')}", required=True
                    )
                sub_parser_action.add_argument("--sudo", required=False)

            required, optional, dummy = custom_actions[name][action_name]
            for x in required:
                if x != obj_cls._id_attr:
                    sub_parser_action.add_argument(
                        f"--{x.replace('_', '-')}", required=True
                    )
            for x in optional:
                if x != obj_cls._id_attr:
                    sub_parser_action.add_argument(
                        f"--{x.replace('_', '-')}", required=False
                    )


class _comp_first_name:
    def __call__(self, obj: Tuple[Type[RestfulObject], Type[RestfulManager]]):
        return obj[0].__name__


def extend_resources_parser(
    subparsers: _SubparserType,
    classes: List[Tuple[Type[RestfulObject], Type[RestfulManager]]],
    action_name: str = "resource_action",
) -> _SubparserType:
    for obj_cls, manager in sorted(classes, key=_comp_first_name):
        name = to_dasherized_lowercase(obj_cls.__name__)
        action_group = subparsers.add_parser(name)

        action_subparsers = action_group.add_subparsers(
            title="action",
            dest=action_name,
            help="Action to execute on the obj_cls.",
        )
        _populate_sub_parser_by_class(obj_cls, manager, action_subparsers)
        action_subparsers.required = True
