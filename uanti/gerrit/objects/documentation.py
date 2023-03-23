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

from uanti.restful.base import RestfulObject, RestfulManager
from uanti.restful.mixins import ListMixin


__all__ = [
    # Documentation Search Endpoints -> Search Documentation
    "DocResult",
    "DocumentationRestfulManager",
]


class DocResult(RestfulObject):
    _id_attr = None


class DocumentationRestfulManager(ListMixin, RestfulManager):
    _path = "/Documentation/"
    _obj_cls = DocResult
