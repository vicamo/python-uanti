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

from uanti.restful.base import RestfulObject, RestfulManager
from uanti.restful.mixins import (
    CreateMixin,
    DeleteMixin,
    GetMixin,
    ListMixin,
)
from uanti.restful.types import RequiredOptional


__all__ = [
    # Account Endpoints -> Create, Delete, Get, Query Account
    "Account",
    "AccountsRestfulManager",
]


class Account(RestfulObject):
    _id_attr = "_account_id"

    def __init__(
        self,
        manager: "RestfulManager",
        attrs: Dict[str, Any],
    ) -> None:
        # Remove additional mark from server query changes result
        if "_more_accounts" in attrs:
            attrs.pop("_more_accounts")

        super().__init__(manager, attrs)


class AccountsRestfulManager(
    CreateMixin, DeleteMixin, GetMixin, ListMixin, RestfulManager
):
    _path = "/accounts/"
    _obj_cls = Account
    _create_attrs = RequiredOptional(
        optional=(
            "username",
            "name",
            "display_name",
            "email",
            "ssh_key",
            "http_password",
            "groups",
        ),
    )
