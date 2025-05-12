"""Script for Fixture Placement"""

from __future__ import annotations

from typing import Any

import NemAll_Python_IFW_Input as AllplanIFW

from BaseInteractor import BaseInteractor
from BuildingElement import BuildingElement
from BuildingElementComposite import BuildingElementComposite
from BuildingElementControlProperties import BuildingElementControlProperties
from StringTableService import StringTableService
from TypeCollections.ModificationElementList import ModificationElementList

from .interactors import PypPlacementInteractor


def check_allplan_version(_build_ele: BuildingElement, version: float) -> bool:
    """Check the current Allplan version

    Args:
        _build_ele: the building element.
        version:    the current Allplan version

    Returns:
        True if compatible with the used Allplan version, false otherwise
    """

    return float(version) >= 2025     #script is compatible only with Allplan 2025 and newer


def create_interactor(coord_input        : AllplanIFW.CoordinateInput,
                      pyp_path           : str,
                      str_table_service  : StringTableService,
                      build_ele_list     : list[BuildingElement],
                      build_ele_composite: BuildingElementComposite,
                      control_props_list : list[BuildingElementControlProperties],
                      _modify_uuid_list  : ModificationElementList) -> Any                 :
    """Create the interactor

    Args:
        coord_input:                coordinate input
        pyp_path:                   path of the pyp file
        str_table_service:          global string table service
        build_ele_list:             building element list
        build_ele_composite:        building element composite
        control_props_list:         control properties list
        _modify_uuid_list:          UUIDs of the existing elements in the modification mode

      Returns:
          Created interactor object
      """
    return PypPlacementInteractor(coord_input, pyp_path, str_table_service, build_ele_list, build_ele_composite, control_props_list)
