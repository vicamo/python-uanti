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

import argparse

from uanti import __app_name__
from uanti.gerrit.cli import extend_resources_parser
from uanti.gerrit import objects


def get_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Gerrit API Command Line Interface",
        allow_abbrev=False,
    )

    parser.add_argument(
        "--version", help=f"Print {__app_name__} version.", action="store_true"
    )

    subparsers = extend_resources_parser(
        parser.add_subparsers(
            title="resource",
            dest="gerrit_resource",
            help="The Gerrit resource to manipulate.",
        ),
        [(objects.Change, objects.ChangesRestfulManager)],
    )
    subparsers.required = True

    return parser


def main() -> None:
    parser = get_parser()

    try:
        import argcomplete  # type: ignore

        argcomplete.autocomplete(parser)  # pragma: no cover
    except Exception:
        pass

    parser.parse_args()
