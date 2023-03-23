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

from typing import Any, Dict, Optional

import urllib.parse

from uanti.restful.base import RestfulObject, RestfulManager
from uanti.restful.mixins import (
    CreateMixin,
    DeleteMixin,
    GetMixin,
    GetWithoutIdMixin,
    ListMixin,
)
from uanti.restful.types import RequiredOptional


__all__ = [
    # Change Endpoints -> Get Meta Diff
    "ChangesMetaDiff",
    "ChangesMetaDiffRestfulManager",
    # Change Endpoints -> Create, Delete, Get, Query Change
    "Change",
    "ChangesRestfulManager",
]


class ChangesMetaDiff(RestfulObject):
    _id_attr: None

    def __init__(
        self,
        manager: "RestfulManager",
        attrs: Dict[str, Any],
    ) -> None:
        super().__init__(manager, attrs)

        self.__dict__["_attrs"]["old_change_info"] = Change(
            self._manager._client.changes,
            self.__dict__["_attrs"]["old_change_info"],
        )
        self.__dict__["_attrs"]["new_change_info"] = Change(
            self._manager._client.changes,
            self.__dict__["_attrs"]["new_change_info"],
        )


class ChangesMetaDiffRestfulManager(GetWithoutIdMixin, RestfulManager):
    _path = "/changes/{change_id}/meta_diff"
    _obj_cls = ChangesMetaDiff
    _from_parent_attrs = {"change_id": "id"}

    def get(
        self,
        meta: Optional[str] = None,
        old: Optional[str] = None,
    ) -> RestfulObject:
        """Retrieves the difference between two historical states of a change.

        Args:
            meta: SHA-1 string of a latter revision. If not provided, the
                current state of the change is used.
            old: SHA-1 string of a former revision. If not provided, the parent
                of the ``meta`` SHA-1 is used.

        Returns:
            The generated RestfulObject

        Raises:
            RestfulAuthenticationError: If authentication is not correct
            RestfulGetError: If the server cannot perform the request
        """
        data = {}

        if meta:
            data["meta"] = meta
        if old:
            data["old"] = old

        return super().get(**data)


class Change(RestfulObject):
    meta_diff: ChangesMetaDiffRestfulManager

    def __init__(
        self,
        manager: "RestfulManager",
        attrs: Dict[str, Any],
    ) -> None:
        # id string returned from server is encoded, so decode it first
        attrs["id"] = urllib.parse.unquote(attrs["id"])
        # Remove additional mark from server query changes result
        if "_more_changes" in attrs:
            attrs.pop("_more_changes")

        super().__init__(manager, attrs)


class ChangesRestfulManager(
    CreateMixin, DeleteMixin, GetMixin, ListMixin, RestfulManager
):
    _path = "/changes/"
    _obj_cls = Change
    _create_attrs = RequiredOptional(
        required=(
            "project",
            "branch",
            "subject",
        ),
        optional=(
            "topic",
            "status",
            "is_private",
            "work_in_progress",
            "base_change",
            "base_commit",
            "new_branch",
            "validation_options",
            "merge",
            "author",
            "notify",
            "notify_details",
        ),
    )
