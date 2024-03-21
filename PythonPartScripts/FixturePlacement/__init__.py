"""
Script for Fixture Placement
"""

from __future__ import annotations

import os
from typing import Any

import NemAll_Python_BaseElements as AllplanBaseElements
import NemAll_Python_Geometry as AllplanGeo
import NemAll_Python_IFW_ElementAdapter as AllplanElementAdapter
import NemAll_Python_IFW_Input as AllplanIFW
from BaseInteractor import BaseInteractor
from BuildingElement import BuildingElement
from BuildingElementComposite import BuildingElementComposite
from BuildingElementControlProperties import BuildingElementControlProperties
from BuildingElementPaletteService import BuildingElementPaletteService
from StringTableService import StringTableService
from VisualScriptService import VisualScriptService

from .SnapToSolid import SnapToSolid

print('FixturePlacement.py Loaded')

def check_allplan_version(_build_ele, version):
    """
    Check the current Allplan version

    Args:
        _build_ele: the building element.
        version:    the current Allplan version

    Returns:
        True/False if version is supported by this script
    """

    # Support all versions
    return float(version) >= 2024

def create_interactor(coord_input        : AllplanIFW.CoordinateInput,
                      _pyp_path          : str,
                      str_table_service  : StringTableService,
                      build_ele_list     : list[BuildingElement],
                      build_ele_composite: BuildingElementComposite,
                      control_props_list : list[BuildingElementControlProperties],
                      _modify_uuid_list  : list) -> Any                 :
    """
    Create the interactor

    Args:
        coord_input:               coordinate input
        _pyp_path:                 path of the pyp file
        global_str_table_service:  global string table service
        build_ele_list:            building element list
        build_ele_composite:       building element composite
        control_props_list:        control properties list
        _modify_uuid_list:         UUIDs of the existing elements in the modification mode

      Returns:
          Created interactor object
      """
    return FixturePlacementInteractor(coord_input, _pyp_path, str_table_service, build_ele_list, build_ele_composite,
                                      control_props_list)


class FixturePlacementInteractor(BaseInteractor):
    """
    Definition of class WallGeometryInteractor
    """

    def __init__(self,
                 coord_input        : AllplanIFW.CoordinateInput,
                 pyp_path           : str,
                 str_table_service  : StringTableService,
                 build_ele_list     : list[BuildingElement],
                 build_ele_composite: BuildingElementComposite,
                 control_props_list : list[BuildingElementControlProperties]):
        """
        Initialization of class WallGeometryInteractor

        Args:
            coord_input:            coordinate input
            pyp_path:               path of the pyp file
            str_table_service:      string table service
            build_ele_list:         list with building elements
            build_ele_composite:    building element composite
            control_props_list:     list with control properties
        """
        self.coord_input              = coord_input
        self.doc                      = self.coord_input.GetInputViewDocument()
        self.pyp_path                 = pyp_path
        self.str_table_service        = str_table_service
        self.first_point_input        = True
        self.first_point              = AllplanGeo.Point3D()
        self.placement_matrix         = AllplanGeo.Matrix3D()
        self.placement_angle          = AllplanGeo.Angle()
        self.placement_point          = AllplanGeo.Point3D()
        self.reference_element        = AllplanElementAdapter.BaseElementAdapter()
        self.build_ele_list           = build_ele_list
        self.build_ele                = self.build_ele_list[0]
        self.control_props_list       = control_props_list
        self.fixture_file_path        = ""
        self.visual_script_service    = None
        self.snap                     = SnapToSolid(self.coord_input)

        # initialize the service for the main palette
        self.main_palette_service = BuildingElementPaletteService(self.build_ele_list,
                                                                  build_ele_composite,
                                                                  None,
                                                                  self.control_props_list,
                                                                  pyp_path)

        # show the main palette and message in the dialog line
        self.main_palette_service.show_palette(self.build_ele_list[0].script_name)
        self.coord_input.InitFirstElementInput(AllplanIFW.InputStringConvert("Select fixture to place"))

    def create_vs_service(self, visual_script_path: str) -> VisualScriptService:
        """ create the service for the VS script

        Returns:
            created script service
        """
        return VisualScriptService(self.coord_input,
                                   visual_script_path,
                                   self.str_table_service,
                                   self.build_ele_list,
                                   self.control_props_list,
                                   [])

    def on_preview_draw(self):
        """ Called when an input in the dialog line is done (e.g. input of a coordinate or rotation angle).
        Gets the new coordinates or angle and updates the preview.
        """

        # update the placement, when a coordinate input in the dialog line was done
        self.placement_point     = self.coord_input.GetCurrentPoint().GetPoint()
        self.placement_angle.Rad = self.coord_input.GetInputControlValue()

        if self.build_ele_list[0].SnapByRadioGroup.value == "SnapByRay":
            self.placement_matrix = self.snap.snap_by_ray(self.placement_point,
                                                          self.placement_angle)
        else:
            self.placement_matrix = self.snap.snap_by_point(self.placement_point,
                                                            self.placement_angle)

        self.draw_preview()

    def modify_element_property(self,
                                page: int,
                                name: str,
                                value: Any):
        """Called after every property modification in the property pallette

        Args:
            page:   the page of the property
            name:   the name of the property
            value:  new value for property
        """
        # when visual script is loaded, pass the argument to the visual script
        if name == "SnapByRadioGroup" and value == "SnapByRay":
            AllplanIFW.HighlightService.CancelAllHighlightedElements(self.coord_input.GetInputViewDocumentID())
        if self.visual_script_service is not None:
            print("modify_element for visual_script_service...")
            self.visual_script_service.modify_element_property(page, name, value)
        else:
            print("modify_element for main_palette_service...")
            if self.main_palette_service.modify_element_property(page, name, value):
                self.main_palette_service.update_palette(-1, False)

    def on_value_input_control_enter(self) -> bool:
        """Handles the enter inside the value input control event

        Returns:
            True/False for success.
        """

        return False

    def on_control_event(self, event_id: int):
        """ Handles the on control event

        Args:
            event_id: event id of button control.
        """
        # when a VS is loaded, do the same as during input in the dialog line
        if self.visual_script_service is not None:
            self.visual_script_service.on_control_event(event_id)

    def on_mouse_leave(self):
        """ Called when the mouse leaves the viewport window.
        The preview is drawn in its last position."""
        if self.visual_script_service is not None:
            self.on_preview_draw()

    def set_active_palette_page_index(self, active_page_index: int):
        """ Called page in the property palette was changed, but also when a dialog
        (e.g. open file dialog) is closed.

        Args:
            active_page_index: index of the active page, starting from 0
        """

        # when after closing the dialog for .pyp file selection a new and non-empty path is detected,
        # the visual script service is initialized
        if active_page_index == 0 and \
                self.build_ele_list[0].FixtureFilePath.value != "" and \
                self.fixture_file_path != self.build_ele.FixtureFilePath.value:

            self.fixture_file_path = self.build_ele.FixtureFilePath.value
            # close the initial palette
            self.main_palette_service.close_palette()

            # initialize the palette with control properties of the visual script
            self.visual_script_service = self.create_vs_service(self.fixture_file_path)

            # initialize the coordinate input for the fixture placement
            self.init_placement_coord_input()

    def on_cancel_function(self) -> bool:
        """Check for input function cancel in case of ESC

        Returns:
            True when python part can be closed after the event, False when it should still run
        """

        if self.visual_script_service is not None:
            # terminate the visual script and show the main palette
            self.visual_script_service = None
            self.build_ele_list[0].FixtureFilePath.value = ""

            # show the initial palette
            self.main_palette_service.refresh_palette(self.build_ele_list, self.control_props_list)
            self.main_palette_service.update_palette(-1, True)
            self.coord_input.InitFirstElementInput(AllplanIFW.InputStringConvert("Select fixture to place"))

            return False

        self.main_palette_service.close_palette()
        return True

    def on_cancel_by_menu_function(self):
        """ Called when the user has started another menu function during the runtime of
        the PythonPart. All the palettes are closed and the PythonPart is terminated.

        """
        if self.visual_script_service is not None:
            self.visual_script_service.on_cancel_function()

        self.main_palette_service.close_palette()

    def process_mouse_msg(self,
                          mouse_msg: int,
                          pnt      : AllplanGeo.Point2D,
                          msg_info : AllplanIFW.AddMsgInfo) -> bool:
        """Process the mouse message event

        Args:
            mouse_msg:  the mouse message.
            pnt:        the input point in view coordinates
            msg_info:   additional message info.

        Returns:
            True/False for success.
        """

        # do nothing, if no fixture specified
        if self.visual_script_service is None:
            return True

        self.placement_point = self.coord_input.GetInputPoint(mouse_msg, pnt, msg_info).GetPoint()

        if self.coord_input.IsMouseMove(mouse_msg):
            if self.build_ele_list[0].SnapByRadioGroup.value == "SnapByRay":
                self.placement_matrix = self.snap.snap_by_ray(self.placement_point,
                                                              self.placement_angle,
                                                              mouse_msg, msg_info)
            else:
                self.placement_matrix = self.snap.snap_by_point(self.placement_point,
                                                                self.placement_angle,
                                                                mouse_msg, pnt, msg_info)

        self.draw_preview()

        if not self.coord_input.IsMouseMove(mouse_msg):

            self.create_elements()

            self.init_placement_coord_input()

        return True

    def create_elements(self):
        """Create the elements in the database

        TODO:
            -   elements should be created all at once
            -   attributes should be assigned before creation
        """
        vs_python_part_elements = self.visual_script_service.create_pythonpart(AllplanGeo.Matrix3D(),
                                                                               AllplanGeo.Matrix3D())


        # Creating the PythonPart in the model, when mouse click detected
        # TODO: create one list with model_elements (pythonpart + recess) and create them at the end of the script
        elements = AllplanBaseElements.CreateElements(doc           = self.coord_input.GetInputViewDocument(),
                                                      insertionMat  = self.placement_matrix,
                                                      modelEleList  = vs_python_part_elements,
                                                      modelUuidList = [],
                                                      assoRefObj    = None)

    def init_placement_coord_input(self):
        """Initialize the coordinate input with the correct settings"""

        prompt = AllplanIFW.InputStringConvert("Place the fixture; rotation around Z axis:")

        # Initialize point input for placing a fixture with with an edit control for angle input
        # The angle is used to rotate the fixture around its local Z axis
        input_control = AllplanIFW.ValueInputControlData(AllplanIFW.eValueInputControlType.eANGLE_COMBOBOX,
                                                         bSetFocus     = True,
                                                         bDisableCoord = False)

        self.coord_input.InitFirstPointValueInput(prompt, input_control)

    def draw_preview(self):
        """Draw the element preview in the viewport using current values for the placement point,
        normal vector and additional rotation"""

        if self.visual_script_service is not None:
            AllplanBaseElements.DrawElementPreview(self.coord_input.GetInputViewDocument(),
                                                   self.placement_matrix,
                                                   self.visual_script_service.get_preview_elements(),
                                                   bDirectDraw  = False,    # FIXME: preview is not shown in the UVS
                                                   assoRefObj   = None)
