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

"""Root Tastypie API class."""

from typing import Any, Dict, Optional, Type, Union

from requests.auth import AuthBase
import requests
from urllib.parse import urlparse, urlunparse, ParseResult

from uanti.restful.base import RestfulManager
from uanti.restful.client import RestfulClient
from uanti.restful import exceptions as exc
from uanti.restful.mixins import (
    CreateMixin,
    DeleteMixin,
    GetMixin,
    ListMixin,
    UpdateMixin,
)
from uanti.restful.types import RequiredOptional

from .base import TastypieRestfulObject


class Tastypie(RestfulClient):
    """Root Tastypie API class.

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

    _manager_map = {}

    def __init__(
        self,
        url: str = None,
        auth: Optional[AuthBase] = None,
        ssl_verify: Union[bool, str] = True,
        timeout: Optional[float] = None,
        user_agent: str = None,
        retry_transient_errors: bool = False,
        session: Optional[requests.Session] = None,
    ) -> None:
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

    def _create_manager(
        self,
        resource: str,
        resource_info: Dict[str, Any],
        parsed_url: ParseResult,
    ) -> Type:
        list_url = urlunparse(
            parsed_url._replace(path=resource_info['list_endpoint'])
        )
        schema = resource_info['schema']

        # TODO:
        #   - allowed_detail_http_methods: patch
        #   - allowed_list_http_methods
        #   - default_format: always assume application/json
        #   - fields
        #     - default: don't care
        #     - help_text: don't care
        #     - nullable: don't care
        #     - resource_uri
        #     - type: don't care
        #     - unique: don't care
        #     - verbose_name: don't care
        #   - list
        #     - default_limit
        #     - filtering

        object_cls_attr = {'_id_attr': None, '_related_attrs': {}}
        manager_cls_create_required = []
        manager_cls_create_optional = []
        manager_cls_create_exclusive = []

        for field, field_info in schema['fields'].items():
            if field_info['readonly']:
                manager_cls_create_exclusive.append(field)
            elif field_info['blank']:
                manager_cls_create_optional.append(field)
            else:
                manager_cls_create_required.append(field)

            if field_info['primary_key']:
                object_cls_attr['_id_attr'] = field

            if 'related_schema' in field_info:
                object_cls_attr['_related_attrs'][field] = {
                    'related_type': field_info['related_type'],
                    'path': urlunparse(
                        parsed_url._replace(path=field_info['related_schema'])
                    )
                    .removeprefix(self._url)
                    .removesuffix('schema/'),
                }

        object_cls = type(
            resource.capitalize(), (TastypieRestfulObject,), object_cls_attr
        )

        manager_cls_attr = {}
        manager_cls_attr['_path'] = list_url.removeprefix(self._url)
        manager_cls_attr['_obj_cls'] = object_cls

        manager_base = []
        allowed_detail_http_methods = schema['allowed_detail_http_methods']
        if 'post' in allowed_detail_http_methods:
            manager_base.append(CreateMixin)
            manager_cls_attr['_create_attrs'] = RequiredOptional(
                required=tuple(manager_cls_create_required),
                optional=tuple(manager_cls_create_optional),
                exclusive=tuple(manager_cls_create_exclusive),
            )
        if 'delete' in allowed_detail_http_methods:
            manager_base.append(DeleteMixin)
        if 'put' in allowed_detail_http_methods:
            manager_base.append(UpdateMixin)
            manager_cls_attr['_update_uses_post'] = False
            manager_cls_attr['_update_attrs'] = RequiredOptional(
                required=tuple(manager_cls_create_required),
                optional=tuple(manager_cls_create_optional),
                exclusive=tuple(manager_cls_create_exclusive),
            )
        if (
            'get' in allowed_detail_http_methods
            and object_cls_attr['_id_attr'] is not None
        ):
            manager_base.append(GetMixin)
        manager_base.append(RestfulManager)

        manager_cls = type(
            ''.join([s.capitalize() for s in resource.split('/')]) + 'Manager',
            tuple(manager_base),
            manager_cls_attr,
        )

        self.__dict__[resource] = manager_cls(self)

        return manager_cls

    def load_api(self, skip_failed: bool = False) -> None:
        resources = self.http_get(self._url, query_data={'fullschema': 'true'})

        if self._url not in Tastypie._manager_map:
            Tastypie._manager_map[self._url] = {}
        manager_map = Tastypie._manager_map[self._url]

        parsed_url = urlparse(self._url)
        for resource, resource_info in resources.items():
            if resource in manager_map:
                self.__dict__[resource] = manager_map[resource](self)
                continue

            try:
                manager_map[resource] = self._create_manager(
                    resource, resource_info, parsed_url
                )
            except Exception as e:
                if skip_failed:
                    pass
                else:
                    raise exc.RestfulParsingError(
                        error_message="Failed to parse the server message"
                    ) from e
