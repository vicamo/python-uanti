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

from typing import Any, Dict

import urllib.parse

from uanti.restful.base import RestfulObject, RestfulManager
from uanti.restful.mixins import (
    CreateMixin,
    DeleteMixin,
    GetMixin,
    ListMixin,
)
from uanti.restful.types import RequiredOptional


__all__ = [
    # Group Endpoints -> Create, Delete, Get, List, Query Group
    "Group",
    "GroupsRestfulManager",
]


class Group(RestfulObject):
    def __init__(
        self,
        manager: "RestfulManager",
        attrs: Dict[str, Any],
    ) -> None:
        # id, owner_id strings returned from server is encoded
        for attr in ("id", "owner_id"):
            attrs[attr] = urllib.parse.unquote(attrs[attr])
        # Remove additional mark from server query changes result
        if "_more_groups" in attrs:
            attrs.pop("_more_groups")

        super().__init__(manager, attrs)


class GroupsRestfulManager(
    CreateMixin, DeleteMixin, GetMixin, ListMixin, RestfulManager
):
    _path = "/groups/"
    _obj_cls = Group
    _create_attrs = RequiredOptional(
        optional=(
            "name",
            "uuid",
            "description",
            "visible_to_all",
            "owner_id",
            "members",
        ),
    )
