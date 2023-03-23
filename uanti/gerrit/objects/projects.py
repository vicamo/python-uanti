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
from uanti.restful.mixins import CreateMixin, GetMixin, ListFromDictMixin
from uanti.restful.types import RequiredOptional


__all__ = [
    # Project Endpoints -> Create, Get, List, Query Project
    "Project",
    "ProjectsRestfulManager",
]


class Project(RestfulObject):
    def __init__(
        self,
        manager: "RestfulManager",
        attrs: Dict[str, Any],
    ) -> None:
        # id string returned from server is encoded, so decode it first
        attrs["id"] = urllib.parse.unquote(attrs["id"])

        super().__init__(manager, attrs)


class ProjectsRestfulManager(
    CreateMixin,
    GetMixin,
    ListFromDictMixin,
    RestfulManager,
):
    _path = "/projects/"
    _obj_cls = Project
    _create_attrs = RequiredOptional(
        optional=(
            "name",
            "parent",
            "description",
            "permissions_only",
            "create_empty_commit",
            "submit_type",
            "branches",
            "owners",
            "use_contributor_agreements",
            "use_signed_off_by",
            "create_new_change_for_all_not_in_target",
            "use_content_merge",
            "require_change_id",
            "enable_signed_push",
            "require_signed_push",
            "max_object_size_limit",
            "plugin_config_values",
            "reject_empty_commit",
        ),
    )
