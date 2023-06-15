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

from uanti.restful.base import RestfulObject


class TastypieRestfulObject(RestfulObject):
    def __init__(
        self,
        manager: "RestfulManager",
        attrs: Dict[str, Any],
    ) -> None:
        super().__init__(manager, attrs)

        client = self._manager._client
        managers = client._manager_map[client._url]
        for field, field_options in self.__class__._related_attrs.items():
            if (
                field not in self.__dict__['_attrs']
                or self.__dict__['_attrs'][field] is None
            ):
                continue

            for resource, manager_cls in managers.items():
                if field_options['path'] != manager_cls._path:
                    continue

                if field_options['related_type'] == 'to_one':
                    self.__dict__['_attrs'][field] = manager_cls._obj_cls(
                        client.__dict__[resource],
                        self.__dict__['_attrs'][field],
                    )
                else:  # 'to_many'
                    self.__dict__['_attrs'][field] = [
                        manager_cls._obj_cls(client.__dict__[resource], data)
                        for data in self.__dict__['_attrs'][field]
                    ]

                break
