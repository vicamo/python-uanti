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

from typing import Any, Dict, Union

import re

import urllib.parse


def copy_dict(
    *,
    src: Dict[str, Any],
    dest: Dict[str, Any],
) -> None:
    for k, v in src.items():
        if isinstance(v, dict):
            # NOTE(jlvillal): This provides some support for the `hash` type
            # https://docs.gitlab.com/ee/api/#hash
            # Transform dict values to new attributes. For example:
            # custom_attributes: {'foo', 'bar'} =>
            #   "custom_attributes['foo']": "bar"
            for dict_k, dict_v in v.items():
                dest[f"{k}[{dict_k}]"] = dict_v
        else:
            dest[k] = v


class EncodedId(str):
    """A custom `str` class that will return the URL-encoded value of the
    string.

      * Using it recursively will only url-encode the value once.
      * Can accept either `str` or `int` as input value.
      * Can be used in an f-string and output the URL-encoded string.

    Reference to documentation on why this is necessary.

    See::

        https://docs.gitlab.com/ee/api/index.html#namespaced-path-encoding
        https://docs.gitlab.com/ee/api/index.html#path-parameters
    """

    def __new__(cls, value: Union[str, int, "EncodedId"]) -> "EncodedId":
        if isinstance(value, EncodedId):
            return value

        if not isinstance(value, (int, str)):
            raise TypeError(f"Unsupported type received: {type(value)}")
        if isinstance(value, str):
            value = urllib.parse.quote(value, safe="")
        return super().__new__(cls, value)


# This regex is based on:
# https://github.com/jpvanhal/inflection/blob/master/inflection/__init__.py
_camel_upperlower_regex = re.compile(r"([A-Z]+)([A-Z][a-z])")
_camel_lowerupper_regex = re.compile(r"([a-z\d])([A-Z])")


def to_dasherized_lowercase(name: str) -> str:
    dasherized_uppercase = _camel_upperlower_regex.sub(r"\1-\2", name)
    dasherized_lowercase = _camel_lowerupper_regex.sub(
        r"\1-\2", dasherized_uppercase
    )
    return dasherized_lowercase.lower()
