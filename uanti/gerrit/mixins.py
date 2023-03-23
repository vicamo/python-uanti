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
)

from uanti.restful import base, client
from uanti.restful import exceptions as exc

__all__ = [
    "GerritRestfulObjectList",
    "GerritListMixin",
]


class GerritRestfulObjectList(base.RestfulObjectList):
    pass


class GerritListMixin(base.RestfulManager):
    _from_parent_attrs: Dict[str, Any]
    _list_filters: Tuple[str, ...] = ()
    _obj_cls: Optional[Type[base.RestfulObject]]
    _parent: Optional[base.RestfulObject]
    _parent_attrs: Dict[str, Any]
    _path: Optional[str]
    _client: client.RestfulClient

    @exc.on_http_error(exc.RestfulListError)
    def list(
        self,
        n: Optional[int] = 0,
        start: Optional[int] = 0,
        **kwargs: Any,
    ) -> List[base.RestfulObject]:
        """Retrieve a list of objects.

        Args:
            n: Limit the returned results. Use -1 to remove the default limit
                on queries and return all.
            start: Skip a number of changes.
            **kwargs: Extra options to send to the server (e.g. sudo)

        Returns:
            The list of objects

        Raises:
            RestfulAuthenticationError: If authentication is not correct
            RestfulListError: If the server cannot perform the request
        """

        data = kwargs.copy()

        # Allow to overwrite the path, handy for custom listings
        path = data.pop("path", self.path)

        if n == -1:
            data["no-limit"] = True
        if start != 0:
            data["start"] = start

        if TYPE_CHECKING:
            assert self._obj_cls is not None
        results = self._client.http_list(path, **data)
        if TYPE_CHECKING:
            assert not isinstance(results, list)
        return GerritRestfulObjectList(self, self._obj_cls, results)
