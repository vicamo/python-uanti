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

import importlib

from types import ModuleType
from typing import Any, Dict, Iterable, Optional, Type, TYPE_CHECKING, Union

import copy
import json
import pprint
import textwrap

from .client import RestfulClient
from .types import RequiredOptional
from .utils import EncodedId
from uanti.restful import exceptions as exc

__all__ = [
    "RestfulObject",
    "RestfulManager",
]


class RestfulObject:
    """Represents an object built from server data.

    It holds the attributes know from the server, and the updated attributes in
    another. This allows smart updates, if the object allows it.

    You can redefine ``_id_attr`` in child classes to specify which attribute
    must be used as the unique ID. ``None`` means that the object can be
    updated without ID in the url.

    Likewise, you can define a ``_repr_attr`` in subclasses to specify which
    attribute should be added as a human-readable identifier when called in the
    object's ``__repr__()`` method.
    """

    _id_attr: Optional[str] = "id"
    _attrs: Dict[str, Any]
    _created_from_list: bool  # Indicates if object was created from a list()
    _module: ModuleType
    _parent_attrs: Dict[str, Any]
    _repr_attr: Optional[str] = None
    _updated_attrs: Dict[str, Any]
    _manager: "RestfulManager"

    def __init__(
        self,
        manager: "RestfulManager",
        attrs: Dict[str, Any],
        *,
        created_from_list: bool = False,
    ) -> None:
        if not isinstance(attrs, dict):
            raise exc.RestfulParsingError(
                f"Attempted to initialize RestfulObject with a non-dictionary "
                f"value: {attrs!r}\nThis likely indicates an incorrect or "
                f"malformed server response."
            )
        self.__dict__.update(
            {
                "_manager": manager,
                "_attrs": attrs,
                "_updated_attrs": {},
                "_module": importlib.import_module(self.__module__),
                "_created_from_list": created_from_list,
            }
        )
        self.__dict__["_parent_attrs"] = self._manager.parent_attrs
        self._create_managers()

    def __getattr__(self, name: str) -> Any:
        if name in self.__dict__["_updated_attrs"]:
            return self.__dict__["_updated_attrs"][name]

        if name in self.__dict__["_attrs"]:
            value = self.__dict__["_attrs"][name]
            # If the value is a list, we copy it in the _updated_attrs dict
            # because we are not able to detect changes made on the object
            # (append, insert, pop, ...). Without forcing the attr
            # creation __setattr__ is never called, the list never ends up
            # in the _updated_attrs dict, and the update() and save()
            # method never push the new data to the server.
            # See https://github.com/python-gitlab/python-gitlab/issues/306
            #
            # note: _parent_attrs will only store simple values (int) so we
            # don't make this check in the next block.
            if isinstance(value, list):
                self.__dict__["_updated_attrs"][name] = value[:]
                return self.__dict__["_updated_attrs"][name]

            return value

        if name in self.__dict__["_parent_attrs"]:
            return self.__dict__["_parent_attrs"][name]

        message = f"{type(self).__name__!r} object has no attribute {name!r}"
        if self._created_from_list:
            message = f"{message}\n\n" + textwrap.fill(
                f"{self.__class__!r} was created via a list() call and "
                f"only a subset of the data may be present. To ensure "
                f"all data is present get the object using a "
                f"get(object.id) call. For more details, see:"
            )
        raise AttributeError(message)

    def __setattr__(self, name: str, value: Any) -> None:
        self.__dict__["_updated_attrs"][name] = value

    def asdict(self, *, with_parent_attrs: bool = False) -> Dict[str, Any]:
        data = {}
        if with_parent_attrs:
            data.update(copy.deepcopy(self._parent_attrs))
        data.update(copy.deepcopy(self._attrs))
        data.update(copy.deepcopy(self._updated_attrs))
        return data

    @property
    def attributes(self) -> Dict[str, Any]:
        return self.asdict(with_parent_attrs=True)

    def to_json(
        self, *, with_parent_attrs: bool = False, **kwargs: Any
    ) -> str:
        return json.dumps(
            self.asdict(with_parent_attrs=with_parent_attrs), **kwargs
        )

    def __str__(self) -> str:
        return f"{type(self)} => {self.asdict()}"

    def pformat(self) -> str:
        return f"{type(self)} => \n{pprint.pformat(self.asdict())}"

    def pprint(self) -> None:
        print(self.pformat())

    def __repr__(self) -> str:
        name = self.__class__.__name__

        if (self._id_attr and self._repr_value) and (
            self._id_attr != self._repr_attr
        ):
            return (
                f"<{name} {self._id_attr}:{self.get_id()} "
                f"{self._repr_attr}:{self._repr_value}>"
            )
        if self._id_attr:
            return f"<{name} {self._id_attr}:{self.get_id()}>"
        if self._repr_value:
            return f"<{name} {self._repr_attr}:{self._repr_value}>"

        return f"<{name}>"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, RestfulObject):
            return NotImplemented
        if self.get_id() and other.get_id():
            return self.get_id() == other.get_id()
        return super() == other

    def __ne__(self, other: object) -> bool:
        if not isinstance(other, RestfulObject):
            return NotImplemented
        if self.get_id() and other.get_id():
            return self.get_id() != other.get_id()
        return super() != other

    def __dir__(self) -> Iterable[str]:
        return set(self.attributes).union(super().__dir__())

    def __hash__(self) -> int:
        if not self.get_id():
            return super().__hash__()
        return hash(self.get_id())

    def _create_managers(self) -> None:
        # NOTE(jlvillal): We are creating our managers by looking at the class
        # annotations. If an attribute is annotated as being a *Manager type
        # then we create the manager and assign it to the attribute.
        for attr, annotation in sorted(self.__annotations__.items()):
            # We ignore creating a manager for the '_manager' attribute as that
            # is done in the self.__init__() method
            if attr in ("_manager",):
                continue
            if not isinstance(annotation, (type, str)):
                continue
            if isinstance(annotation, type):
                cls_name = annotation.__name__
            else:
                cls_name = annotation
            # All *Manager classes are used except for the base
            # "RestfulManager" class
            if cls_name == "RestfulManager" or not cls_name.endswith(
                "RestfulManager"
            ):
                continue
            cls = getattr(self._module, cls_name)
            manager = cls(self._manager._client, parent=self)
            # Since we have our own __setattr__ method, we can't use setattr()
            self.__dict__[attr] = manager

    def _update_attrs(self, new_attrs: Dict[str, Any]) -> None:
        self.__dict__["_updated_attrs"] = {}
        self.__dict__["_attrs"] = new_attrs

    def get_id(self) -> Optional[Union[int, str]]:
        """Returns the id of the resource."""
        if self._id_attr is None or not hasattr(self, self._id_attr):
            return None
        id_val = getattr(self, self._id_attr)
        if TYPE_CHECKING:
            assert id_val is None or isinstance(id_val, (int, str))
        return id_val

    @property
    def _repr_value(self) -> Optional[str]:
        """Safely returns the human-readable resource name if present."""
        if self._repr_attr is None or not hasattr(self, self._repr_attr):
            return None
        repr_val = getattr(self, self._repr_attr)
        if TYPE_CHECKING:
            assert isinstance(repr_val, str)
        return repr_val


class RestfulManager:
    """Base class for CRUD operations on objects.

    Derived class must define ``_path`` and ``_obj_cls``.

    ``_path``: Base URL path on which requests will be sent (e.g. '/projects')
    ``_obj_cls``: The class of objects that will be created
    """

    _create_attrs: RequiredOptional = RequiredOptional()
    _update_attrs: RequiredOptional = RequiredOptional()
    _path: Optional[str] = None
    _obj_cls: Optional[Type[RestfulObject]] = None
    _from_parent_attrs: Dict[str, Any] = {}

    _computed_path: Optional[str]
    _parent: Optional[RestfulObject]
    _parent_attrs: Dict[str, Any]
    _client: RestfulClient

    def __init__(
        self, client: RestfulClient, parent: Optional[RestfulObject] = None
    ) -> None:
        """REST manager constructor.

        Args:
            client: :class:`~uandi.restful.client.RestfulClient` connection to
                use to make requests.
            parent: REST object to which the manager is attached.
        """
        self._client = client
        self._parent = parent  # for nested managers
        self._computed_path = self._compute_path()

    @property
    def parent_attrs(self) -> Optional[Dict[str, Any]]:
        return self._parent_attrs

    def _compute_path(self, path: Optional[str] = None) -> Optional[str]:
        self._parent_attrs = {}
        if path is None:
            path = self._path
        if path is None:
            return None
        if self._parent is None or not self._from_parent_attrs:
            return path

        data: Dict[str, Optional[EncodedId]] = {}
        for self_attr, parent_attr in self._from_parent_attrs.items():
            if not hasattr(self._parent, parent_attr):
                data[self_attr] = None
                continue
            data[self_attr] = EncodedId(getattr(self._parent, parent_attr))
        self._parent_attrs = data
        return path.format(**data)

    @property
    def path(self) -> Optional[str]:
        return self._computed_path
