#
# Copyright (C) 2018 Mostafa Moradian <mostafamoradian0@gmail.com>
#
# This file is part of grest.
#
# grest is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# grest is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with grest.  If not, see <http://www.gnu.org/licenses/>.
#

try:
    # For Python 3.0 and later
    from urllib.request import unquote
except ImportError:
    # Fall back to Python 2's urllib2
    from urllib2 import unquote

from inflection import pluralize, singularize
from markupsafe import escape_silent as escape
from neomodel.exception import DoesNotExist

import grest.messages as msg
from grest.exceptions import HTTPException
from grest.utils import serialize
from grest.validation import validate_models


def get(self, primary_id, secondary_model_name=None, secondary_id=None):
    """
    Returns an specified node or its related node
    :param primary_id: unique id of the primary (src) node (model)
    :type: str
    :param secondary_model_name: name of the secondary (dest) node (model)
    :type: str
    :param secondary_id: unique id of the secondary (dest) node (model)
    :type: str

    The equivalent cypher query would be (as an example):
    MATCH (u:User) WHERE n.user_id = "123456789" RETURN n
    Or:
    MATCH (u:User)-[LIKES]->(p:Post) WHERE n.user_id = "123456789" RETURN p
    """
    try:
        # patch __log
        self.__log = self._GRest__log

        validate_models(self,
                        primary_id,
                        secondary_model_name,
                        secondary_id)

        primary_selected_item = self.primary_model.nodes.get_or_none(
            **{self.primary_selection_field: primary_id})

        if all([self.primary_selected_item,
                self.secondary_model,
                self.secondary_id]):
            # user selected a nested model with 2 keys
            # (from the primary and secondary models)
            # /users/user_id/roles/role_id -> selected role of this user
            # /categories/cat_id/tags/tag_id -> selected tag of this category

            # In this example, the p variable of type Post
            # is the secondary_item
            # (u:User)-[:POSTED]-(p:Post)
            secondary_item = self.primary_selected_item.get_all(
                self.secondary_model_name,
                self.secondary_selection_field,
                self.secondary_id,
                retrieve_relations=True)

            return serialize({singularize(self.secondary_model_name):
                              secondary_item})
        elif all([self.primary_selected_item, self.secondary_model]):
            # user selected a nested model with primary key
            # (from the primary and the secondary models)
            # /users/user_1/roles -> all roles for this user
            relationships = self.primary_selected_item.get_all(
                self.secondary_model_name,
                retrieve_relations=True)
            return serialize({pluralize(self.secondary_model_name):
                              relationships})
        else:
            # user selected a single item (from the primary model)
            if self.primary_selected_item:
                return serialize({self.primary_model_name:
                                  primary_selected_item.to_dict()})
            else:
                raise HTTPException(msg.MODEL_DOES_NOT_EXIST.format(
                    model=self.primary_model_name), 404)
    except (DoesNotExist, AttributeError) as e:
        self.__log.exception(e)
        raise HTTPException(msg.ITEM_DOES_NOT_EXIST, 404)
