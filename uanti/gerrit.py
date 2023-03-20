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

"""Root Gerrit API class."""

__all__ = [
    "Gerrit",
]


from lazr.restfulclient.resource import (
    CollectionWithKeyBasedLookup,
    ServiceRoot,
)

from uanti import const


class ChangesSet(CollectionWithKeyBasedLookup):
    """A custom subclass capable of change lookup by change-id."""

    def _get_url_from_id(self, key):
        """Transform a change-id into the URL to a change resource."""
        return str(self._root._root_uri.ensureSlash()) + "changes/" + str(key)

    collection_of = "change"


class Gerrit(ServiceRoot):
    """Root Gerrit API class."""

    RESOURCE_TYPE_CLASSES = {
        "changes": ChangesSet,
    }
    RESOURCE_TYPE_CLASSES.update(ServiceRoot.RESOURCE_TYPE_CLASSES)

    def __init__(
        self,
        service_root=const.GERRIT_SERVICE_ROOT,
        cache=None,
        timeout=None,
        wadl_markup=None,
    ):
        """Root access to the Gerrit API.

        :param service_root: The URL to the root of the web service.
        :type service_root: string
        """
        super(Gerrit, self).__init__(
            None, service_root, cache=cache, timeout=timeout,
            wadl_markup=wadl_markup
        )
