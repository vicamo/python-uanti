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

import functools
from typing import (
    Any,
    Callable,
    cast,
    Optional,
    Type,
    TYPE_CHECKING,
    TypeVar,
    Union,
)

__all__ = [
    "RestfulError",
    "RestfulHttpError",
    "RestfulParsingError",
    "RestfulRedirectError",
    # operation errors
    "RestfulOperationError",
    "RestfulCreateError",
    "RestfulDeleteError",
    "RestfulGetError",
    "RestfulListError",
    "RestfulUpdateError",
    # misc
    "on_http_error",
]


class RestfulError(Exception):
    def __init__(
        self,
        error_message: Union[str, bytes] = "",
        response_code: Optional[int] = None,
        response_body: Optional[bytes] = None,
    ) -> None:
        Exception.__init__(self, error_message)
        # Http status code
        self.response_code = response_code
        # Full http response
        self.response_body = response_body
        # Parsed error message from gitlab
        try:
            # if we receive str/bytes we try to convert to unicode/str to have
            # consistent message types (see #616)
            if TYPE_CHECKING:
                assert isinstance(error_message, bytes)
            self.error_message = error_message.decode()
        except Exception:
            if TYPE_CHECKING:
                assert isinstance(error_message, str)
            self.error_message = error_message

    def __str__(self) -> str:
        if self.response_code is not None:
            return f"{self.response_code}: {self.error_message}"
        return f"{self.error_message}"


class RestfulAuthenticationError(RestfulError):
    pass


class RestfulHttpError(RestfulError):
    pass


class RestfulParsingError(RestfulError):
    pass


class RestfulRedirectError(RestfulError):
    pass


class RestfulOperationError(RestfulError):
    pass


class RestfulCreateError(RestfulOperationError):
    pass


class RestfulDeleteError(RestfulOperationError):
    pass


class RestfulGetError(RestfulOperationError):
    pass


class RestfulListError(RestfulOperationError):
    pass


class RestfulUpdateError(RestfulOperationError):
    pass


# For an explanation of how these type-hints work see:
# https://mypy.readthedocs.io/en/stable/generics.html#declaring-decorators
#
# The goal here is that functions which get decorated will retain their types.
__F = TypeVar("__F", bound=Callable[..., Any])


def on_http_error(error: Type[Exception]) -> Callable[[__F], __F]:
    """Manage RestfulHttpError exceptions.

    This decorator function can be used to catch RestfulHttpError exceptions
    raise specialized exceptions instead.

    Args:
        The exception type to raise -- must inherit from RestfulError
    """

    def wrap(f: __F) -> __F:
        @functools.wraps(f)
        def wrapped_f(*args: Any, **kwargs: Any) -> Any:
            try:
                return f(*args, **kwargs)
            except RestfulHttpError as e:
                raise error(
                    e.error_message, e.response_code, e.response_body
                ) from e

        return cast(__F, wrapped_f)

    return wrap


__all__ = [name for name in dir() if name.endswith("Error")]
