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

# The MIT License
#
# Copyright 2013 Sony Mobile Communications. All rights reserved.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

"""Authentication handlers."""

from requests.auth import HTTPDigestAuth, HTTPBasicAuth
from requests.utils import get_netrc_auth


__all__ = [
    "HTTPDigestAuthFromNetrc",
    "HTTPBasicAuthFromNetrc",
]


def _get_netrc_auth(url):
    return get_netrc_auth(url)


class HTTPDigestAuthFromNetrc(HTTPDigestAuth):
    """HTTP Digest Auth with netrc credentials."""

    def __init__(self, url):
        """See class docstring."""
        auth = _get_netrc_auth(url)
        if not auth:
            raise ValueError("netrc missing or no credentials found in netrc")
        username, password = auth
        super(HTTPDigestAuthFromNetrc, self).__init__(username, password)


class HTTPBasicAuthFromNetrc(HTTPBasicAuth):
    """HTTP Basic Auth with netrc credentials."""

    def __init__(self, url):
        """See class docstring."""
        auth = _get_netrc_auth(url)
        if not auth:
            raise ValueError("netrc missing or no credentials found in netrc")
        username, password = auth
        super(HTTPBasicAuthFromNetrc, self).__init__(username, password)
