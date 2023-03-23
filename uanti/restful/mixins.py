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
    Dict,
    List,
    Optional,
    Tuple,
    Type,
    TYPE_CHECKING,
    Union,
)

import requests

from uanti.restful import base, client, utils
from uanti.restful import exceptions as exc

__all__ = [
    "GetMixin",
    "ListMixin",
]


class GetMixin(base.RestfulManager):
    _from_parent_attrs: Dict[str, Any]
    _obj_cls: Optional[Type[base.RestfulObject]]
    _optional_get_attrs: Tuple[str, ...] = ()
    _parent: Optional[base.RestfulObject]
    _parent_attrs: Dict[str, Any]
    _path: Optional[str]
    _client: client.RestfulClient

    @exc.on_http_error(exc.RestfulGetError)
    def get(
        self, id: Union[str, int], lazy: bool = False, **kwargs: Any
    ) -> base.RestfulObject:
        """Retrieve a single object.

        Args:
            id: ID of the object to retrieve
            lazy: If True, don't request the server, but create a
                         shallow object giving access to the managers. This is
                         useful if you want to avoid useless calls to the API.
            **kwargs: Extra options to send to the server (e.g. sudo)

        Returns:
            The generated RestfulObject.

        Raises:
            RestfulAuthenticationError: If authentication is not correct
            RestfulGetError: If the server cannot perform the request
        """
        if isinstance(id, str):
            id = utils.EncodedId(id)
        path = f"{self.path}/{id}"
        if TYPE_CHECKING:
            assert self._obj_cls is not None
        if lazy is True:
            if TYPE_CHECKING:
                assert self._obj_cls._id_attr is not None
            return self._obj_cls(self, {self._obj_cls._id_attr: id}, lazy=lazy)
        server_data = self._client.http_get(path, **kwargs)
        if TYPE_CHECKING:
            assert not isinstance(server_data, requests.Response)
        return self._obj_cls(self, server_data, lazy=lazy)


class ListMixin(base.RestfulManager):
    _from_parent_attrs: Dict[str, Any]
    _list_filters: Tuple[str, ...] = ()
    _obj_cls: Optional[Type[base.RestfulObject]]
    _parent: Optional[base.RestfulObject]
    _parent_attrs: Dict[str, Any]
    _path: Optional[str]
    _client: client.RestfulClient

    @exc.on_http_error(exc.RestfulListError)
    def list(self, **kwargs: Any) -> List[base.RestfulObject]:
        """Retrieve a list of objects.

        Args:
            **kwargs: Extra options to send to the server (e.g. sudo)

        Returns:
            The list of objects

        Raises:
            RestfulAuthenticationError: If authentication is not correct
            RestfulListError: If the server cannot perform the request
        """

        # Allow to overwrite the path, handy for custom listings
        path = kwargs.pop("path", self.path)

        if TYPE_CHECKING:
            assert self._obj_cls is not None
        obj = self._client.http_list(path, **kwargs)
        if TYPE_CHECKING:
            assert not isinstance(obj, list)
        return [
            self._obj_cls(self, item, created_from_list=True) for item in obj
        ]
