# Copyright 2023 You-Sheng Yang

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

from typing import Any, List

from uanti.restful.base import RestfulObject, RestfulManager
from uanti.restful.mixins import ListFromDictMixin
from uanti.restful import exceptions as exc


__all__ = [
    # Access Endpoints -> List Access Rights
    "ProjectAccess",
    "AccessRestfulManager",
]


class ProjectAccess(RestfulObject):
    pass


class AccessRestfulManager(ListFromDictMixin, RestfulManager):
    _path = "/access/"
    _obj_cls = ProjectAccess

    @exc.on_http_error(exc.RestfulListError)
    def list(self, **kwargs: Any) -> List[RestfulObject]:
        super().list(copy_id_attr="id", **kwargs)