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

from typing import Any, Dict, Optional, Union

import json
from requests.auth import AuthBase
import requests

from uanti.restful.auth import HTTPBasicAuthFromNetrc
from uanti.restful.client import RestfulClient
from uanti.gerrit import const
from uanti.gerrit import objects


GERRIT_MAGIC_JSON_PREFIX = ")]}'\n"


class Gerrit(RestfulClient):
    """Root Gerrit API class.

    Args:
        url: The URL of the server.
        auth: The authentication handler.
        ssl_verify: Whether SSL certificates should be validated. If
            the value is a string, it is the path to a CA file used for
            certificate validation.
        timeout: Timeout to use for requests to the GitLab server.
        user_agent: A custom user agent to use for making HTTP requests.
        retry_transient_errors: Whether to retry after 500, 502, 503, 504
            or 52x responses. Defaults to False.
        session: The http session to use.
    """

    def __init__(
        self,
        url: str = const.GERRIT_SERVICE_ROOT,
        auth: Optional[AuthBase] = None,
        ssl_verify: Union[bool, str] = True,
        timeout: Optional[float] = None,
        user_agent: str = None,
        retry_transient_errors: bool = False,
        session: Optional[requests.Session] = None,
    ) -> None:
        if not auth:
            try:
                auth = HTTPBasicAuthFromNetrc(url)
            except ValueError:
                pass
        if auth:
            url = url.rstrip("/") + "/a"

        super().__init__(
            url,
            auth,
            ssl_verify,
            timeout,
            user_agent,
            retry_transient_errors,
            session,
        )

        self._headers["Accept"] = "application/json"

        self.changes = objects.ChangesRestfulManager(self)

    def _load_json(self, response: requests.Response) -> Dict[str, Any]:
        """Strip off Gerrit's magic prefix and decode a response.

        :returns:
            Decoded JSON content as a dict, or raw text if content could not be
            decoded as JSON.

        :raises:
            requests.HTTPError if the response contains an HTTP error status
            code.

        """
        content = response.content.strip()
        if response.encoding:
            content = content.decode(response.encoding)
        if not content:
            return content
        if content.startswith(GERRIT_MAGIC_JSON_PREFIX):
            index = len(GERRIT_MAGIC_JSON_PREFIX)
            content = content[index:]

        return json.loads(content)
