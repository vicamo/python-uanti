# Copyright 2023 You-Sheng Yang
# Copyright 2013-2019 Gauvain Pocentek, 2019-2022 python-gitlab team

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

"""uanti.restful package."""


__all__ = [
    "RestfulClient",
]

from typing import Any, Dict, List, Optional, Tuple, TYPE_CHECKING, Union

import time

from urllib import parse
import requests
from requests.auth import AuthBase
from requests_toolbelt.multipart.encoder import MultipartEncoder

from uanti import __title__, __version__
from uanti.restful import utils
from uanti.restful import exceptions as exc


DEFAULT_USER_AGENT: str = f"{__title__}/{__version__}"

REDIRECT_MSG = (
    __title__
    + "detected a {status_code} ({reason!r}) redirection. You must update "
    "your url to the correct url to avoid issues. The redirection was from: "
    "{source!r} to {target!r}"
)

RETRYABLE_TRANSIENT_ERROR_CODES = [500, 502, 503, 504] + list(range(520, 531))


class RestfulClient:
    """Represents a RESTful API server connection.

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
        url: str,
        auth: Optional[AuthBase] = None,
        ssl_verify: Union[bool, str] = True,
        timeout: Optional[float] = None,
        user_agent: str = DEFAULT_USER_AGENT,
        retry_transient_errors: bool = False,
        session: Optional[requests.Session] = None,
    ) -> None:
        self._url = url.rstrip("/")
        self._auth = auth
        self._ssl_verify = ssl_verify
        self._timeout = timeout
        self._headers = {"User-Agent": user_agent}
        self._retry_transient_errors = retry_transient_errors
        self._session = session or requests.Session()

    def __enter__(self) -> "RestfulClient":
        return self

    def __exit__(self, *args: Any) -> None:
        self._session.close()

    def _build_url(self, path: str) -> str:
        """Returns the full url from path.

        If path is already a url, return it unchanged. If it's a path, append
        it to the stored url.

        Returns:
            The full URL
        """
        if path.startswith("http://") or path.startswith("https://"):
            return path
        return f"{self._url}{path}"

    @staticmethod
    def _check_redirects(result: requests.Response) -> None:
        # Check the requests history to detect 301/302 redirections.
        # If the initial verb is POST or PUT, the redirected request will use a
        # GET request, leading to unwanted behaviour.
        # If we detect a redirection with a POST or a PUT request, we
        # raise an exception with a useful error message.
        if not result.history:
            return

        for item in result.history:
            if item.status_code not in (301, 302):
                continue
            # GET methods can be redirected without issue
            if item.request.method == "GET":
                continue
            target = item.headers.get("location")
            raise exc.RestfulRedirectError(
                REDIRECT_MSG.format(
                    status_code=item.status_code,
                    reason=item.reason,
                    source=item.url,
                    target=target,
                )
            )

    @staticmethod
    def _prepare_send_data(
        files: Optional[Dict[str, Any]] = None,
        post_data: Optional[Union[Dict[str, Any], bytes]] = None,
        raw: bool = False,
    ) -> Tuple[
        Optional[Union[Dict[str, Any], bytes]],
        Optional[Union[Dict[str, Any], MultipartEncoder]],
        str,
    ]:
        if files:
            if post_data is None:
                post_data = {}
            else:
                # booleans does not exists for data (neither for
                # MultipartEncoder): cast to string int to avoid: 'bool' object
                # has no attribute 'encode'
                if TYPE_CHECKING:
                    assert isinstance(post_data, dict)
                for k, v in post_data.items():
                    if isinstance(v, bool):
                        post_data[k] = str(int(v))

            for k, v in files.items():
                post_data[k] = v

            data = MultipartEncoder(post_data)
            return (None, data, data.content_type)

        if raw and post_data:
            return (None, post_data, "application/octet-stream")

        if post_data is None:
            post_data = {}

        return (post_data, None, "application/json")

    def _load_json(self, result: requests.Response) -> Dict[str, Any]:
        return result.json()

    def http_request(
        self,
        verb: str,
        path: str,
        query_data: Optional[Dict[str, Any]] = None,
        post_data: Optional[Union[Dict[str, Any], bytes]] = None,
        raw: bool = False,
        streamed: bool = False,
        files: Optional[Dict[str, Any]] = None,
        timeout: Optional[float] = None,
        obey_rate_limit: bool = True,
        retry_transient_errors: Optional[bool] = None,
        max_retries: int = 10,
        **kwargs: Any,
    ) -> requests.Response:
        """Make an HTTP request to the server.

        Args:
            verb: The HTTP method to call ('get', 'post', 'put', 'delete')
            path: Path or full URL to query
            query_data: Data to send as query parameters
            post_data: Data to send in the body (will be converted to
                              json by default)
            raw: If True, do not convert post_data to json
            streamed: Whether the data should be streamed
            files: The files to send to the server
            timeout: The timeout, in seconds, for the request
            obey_rate_limit: Whether to obey 429 Too Many Request
                                    responses. Defaults to True.
            retry_transient_errors: Whether to retry after 500, 502, 503, 504
                or 52x responses. Defaults to False.
            max_retries: Max retries after 429 or transient errors,
                               set to -1 to retry forever. Defaults to 10.
            **kwargs: Extra options to send to the server (e.g. sudo)

        Returns:
            A requests result object.

        Raises:
            RestfulHttpError: When the return code is not 2xx
        """
        query_data = query_data or {}
        raw_url = self._build_url(path)

        # parse user-provided URL params to ensure we don't add our own
        # duplicates
        parsed = parse.urlparse(raw_url)
        params = parse.parse_qs(parsed.query)
        url = parse.urlunparse(parsed._replace(query=""))

        utils.copy_dict(src=query_data, dest=params)
        utils.copy_dict(src=kwargs, dest=params)

        auth = self._auth
        verify = self._ssl_verify

        # If timeout was passed into kwargs, allow it to override the default
        if timeout is None:
            timeout = self._timeout
        if retry_transient_errors is None:
            retry_transient_errors = self._retry_transient_errors

        # We need to deal with json vs. data when uploading files
        headers = self._headers.copy()
        json, data, content_type = self._prepare_send_data(
            files, post_data, raw
        )
        headers["Content-Type"] = content_type

        cur_retries = 0
        while True:
            try:
                result = self._session.request(
                    method=verb,
                    url=url,
                    json=json,
                    data=data,
                    params=params,
                    timeout=timeout,
                    verify=verify,
                    stream=streamed,
                    headers=headers,
                    auth=auth,
                )
            except (
                requests.ConnectionError,
                requests.exceptions.ChunkedEncodingError,
            ):
                if retry_transient_errors and (
                    max_retries == -1 or cur_retries < max_retries
                ):
                    wait_time = 2**cur_retries * 0.1
                    cur_retries += 1
                    time.sleep(wait_time)
                    continue

                raise

            self._check_redirects(result)

            if 200 <= result.status_code < 300:
                return result

            if (429 == result.status_code and obey_rate_limit) or (
                result.status_code in RETRYABLE_TRANSIENT_ERROR_CODES
                and retry_transient_errors
            ):
                # Response headers documentation:
                # https://docs.gitlab.com/ee/user/admin_area/settings/user_and_ip_rate_limits.html#response-headers
                if max_retries == -1 or cur_retries < max_retries:
                    wait_time = 2**cur_retries * 0.1
                    if "Retry-After" in result.headers:
                        wait_time = int(result.headers["Retry-After"])
                    elif "RateLimit-Reset" in result.headers:
                        wait_time = (
                            int(result.headers["RateLimit-Reset"])
                            - time.time()
                        )
                    cur_retries += 1
                    time.sleep(wait_time)
                    continue

            error_message = result.content
            try:
                error_json = self._load_json(result)
                for k in ("message", "error"):
                    if k in error_json:
                        error_message = error_json[k]
            except (KeyError, ValueError, TypeError):
                pass

            if result.status_code == 401:
                raise exc.RestfulAuthenticationError(
                    response_code=result.status_code,
                    error_message=error_message,
                    response_body=result.content,
                )

            raise exc.RestfulHttpError(
                response_code=result.status_code,
                error_message=error_message,
                response_body=result.content,
            )

    def http_get(
        self,
        path: str,
        query_data: Optional[Dict[str, Any]] = None,
        streamed: bool = False,
        raw: bool = False,
        **kwargs: Any,
    ) -> Union[Dict[str, Any], requests.Response]:
        """Make a GET request to the server.

        Args:
            path: Path or full URL to query
            query_data: Data to send as query parameters
            streamed: Whether the data should be streamed
            raw: If True do not try to parse the output as json
            **kwargs: Extra options to send to the server (e.g. sudo)

        Returns:
            A requests result object is streamed is True or the content type is
            not json.
            The parsed json data otherwise.

        Raises:
            RestfulHttpError: When the return code is not 2xx
            RestfulParsingError: If the json data could not be parsed
        """
        query_data = query_data or {}
        result = self.http_request(
            "get", path, query_data=query_data, streamed=streamed, **kwargs
        )

        if (
            result.headers["Content-Type"].split(';')[0] == "application/json"
            and not streamed
            and not raw
        ):
            try:
                json_result = self._load_json(result)
                if TYPE_CHECKING:
                    assert isinstance(json_result, dict)
                return json_result
            except Exception as e:
                raise exc.RestfulParsingError(
                    error_message="Failed to parse the server message"
                ) from e
        else:
            return result

    def http_post(
        self,
        path: str,
        query_data: Optional[Dict[str, Any]] = None,
        post_data: Optional[Dict[str, Any]] = None,
        raw: bool = False,
        files: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Union[Dict[str, Any], requests.Response]:
        """Make a POST request to the server.

        Args:
            path: Path or full URL to query
            query_data: Data to send as query parameters
            post_data: Data to send in the body (will be converted to
                              json by default)
            raw: If True, do not convert post_data to json
            files: The files to send to the server
            **kwargs: Extra options to send to the server (e.g. sudo)

        Returns:
            The parsed json returned by the server if json is return, else the
            raw content

        Raises:
            RestfulHttpError: When the return code is not 2xx
            RestfulParsingError: If the json data could not be parsed
        """
        query_data = query_data or {}
        post_data = post_data or {}

        result = self.http_request(
            "post",
            path,
            query_data=query_data,
            post_data=post_data,
            files=files,
            raw=raw,
            **kwargs,
        )
        try:
            if (
                result.headers["Content-Type"].split(';')[0]
                == "application/json"
            ):
                json_result = self._load_json(result)
                if TYPE_CHECKING:
                    assert isinstance(json_result, dict)
                return json_result
        except Exception as e:
            raise exc.RestfulParsingError(
                error_message="Failed to parse the server message"
            ) from e
        return result

    def http_put(
        self,
        path: str,
        query_data: Optional[Dict[str, Any]] = None,
        post_data: Optional[Union[Dict[str, Any], bytes]] = None,
        raw: bool = False,
        files: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Union[Dict[str, Any], requests.Response]:
        """Make a PUT request to the server.

        Args:
            path: Path or full URL to query
            query_data: Data to send as query parameters
            post_data: Data to send in the body (will be converted to
                              json by default)
            raw: If True, do not convert post_data to json
            files: The files to send to the server
            **kwargs: Extra options to send to the server (e.g. sudo)

        Returns:
            The parsed json returned by the server.

        Raises:
            RestfulHttpError: When the return code is not 2xx
            RestfulParsingError: If the json data could not be parsed
        """
        query_data = query_data or {}
        post_data = post_data or {}

        result = self.http_request(
            "put",
            path,
            query_data=query_data,
            post_data=post_data,
            files=files,
            raw=raw,
            **kwargs,
        )
        try:
            json_result = self._load_json(result)
            if TYPE_CHECKING:
                assert isinstance(json_result, dict)
            return json_result
        except Exception as e:
            raise exc.RestfulParsingError(
                error_message="Failed to parse the server message"
            ) from e

    def http_delete(self, path: str, **kwargs: Any) -> requests.Response:
        """Make a DELETE request to the server.

        Args:
            path: Path or full URL to query
            **kwargs: Extra options to send to the server (e.g. sudo)

        Returns:
            The requests object.

        Raises:
            RestfulHttpError: When the return code is not 2xx
        """
        return self.http_request("delete", path, **kwargs)

    def http_list(
        self,
        path: str,
        query_data: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> List[Dict[str, Any]]:
        """Make a GET request to the server for list-oriented queries.

        Args:
            path: Path or full URL to query
            query_data: Data to send as query parameters
            **kwargs: Extra options to send to the server (e.g. sudo, page,
                      per_page)

        Returns:
            A list of the objects returned by the server.

        Raises:
            RestfulHttpError: When the return code is not 2xx
            RestfulParsingError: If the json data could not be parsed
        """
        url = self._build_url(path)

        result = self.http_request("get", url, query_data=query_data, **kwargs)
        try:
            return self._load_json(result)
        except Exception as e:
            raise exc.RestfulParsingError(
                error_message="Failed to parse the server message"
            ) from e
