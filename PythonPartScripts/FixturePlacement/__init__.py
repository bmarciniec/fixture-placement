"""Script for Fixture Placement"""

from __future__ import annotations

import enum
import os
from typing import Any, cast

import NemAll_Python_BaseElements as AllplanBaseElements
import NemAll_Python_BasisElements as AllplanBasisElements
import NemAll_Python_Geometry as AllplanGeo
import NemAll_Python_IFW_ElementAdapter as AllplanElementAdapter
import NemAll_Python_IFW_Input as AllplanIFW
from BaseInteractor import BaseInteractor
from BuildingElement import BuildingElement
from BuildingElementComposite import BuildingElementComposite
from BuildingElementControlProperties import BuildingElementControlProperties
from BuildingElementPaletteService import BuildingElementPaletteService
from PythonPartTransaction import PythonPartTransaction
from StringTableService import StringTableService
from TypeCollections.ModificationElementList import ModificationElementList
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
    return float(version) >= 2025

def create_interactor(coord_input        : AllplanIFW.CoordinateInput,
                      pyp_path           : str,
                      str_table_service  : StringTableService,
                      build_ele_list     : list[BuildingElement],
                      build_ele_composite: BuildingElementComposite,
                      control_props_list : list[BuildingElementControlProperties],
                      _modify_uuid_list  : ModificationElementList) -> Any                 :
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
    return FixturePlacementInteractor(coord_input, pyp_path, str_table_service, build_ele_list, build_ele_composite,
                                      control_props_list)


class FixturePlacementInteractor(BaseInteractor):
    """Definition of class WallGeometryInteractor"""

    class InputMode(enum.IntEnum):
        """ Definition of the input modes"""
        SELECT  = 0
        """Input mode, where the user selects a VS-PythonPart from the library OR an existing PythonPart """
        PLACE = 1
        """Input mode, where the user places a new VS-PythonPart selected from the library"""
        MOVE = 2
        """Input mode, where the user moves an existing PythonPart with the snap functionality"""


    def __init__(self,
                 coord_input        : AllplanIFW.CoordinateInput,
                 pyp_path           : str,
                 str_table_service  : StringTableService,
                 build_ele_list     : list[BuildingElement],
                 build_ele_composite: BuildingElementComposite,
                 control_props_list : list[BuildingElementControlProperties]):
        """Initialize"""

        self.__input_mode             = self.InputMode.SELECT
        self.coord_input              = coord_input
        self.doc                      = self.coord_input.GetInputViewDocument()
        self.str_table_service        = str_table_service
        self.placement_matrix         = AllplanGeo.Matrix3D()
        self.placement_angle          = AllplanGeo.Angle()
        self.placement_point          = AllplanGeo.Point3D()
        self.selected_pythonpart      = AllplanBasisElements.MacroPlacementElement()
        self.trace_pnt                = AllplanGeo.Point3D()
        self.build_ele_list           = build_ele_list
        self.build_ele                = self.build_ele_list[0]
        self.control_props_list       = control_props_list
        self.visual_script_service    = None
        self.snap                     = SnapToSolid(self.coord_input)

        # initialize the service for the main palette
        self.main_palette_service = BuildingElementPaletteService(self.build_ele_list,
                                                                  build_ele_composite,
                                                                  None,
                                                                  self.control_props_list,
                                                                  pyp_path)
        self.main_palette_service.show_palette(self.build_ele_list[0].script_name)

        self.input_mode             = self.InputMode.SELECT

        # show the main palette and message in the dialog line
        # self.coord_input.InitFirstElementInput(AllplanIFW.InputStringConvert("Select fixture to place"))

    @property
    def pythonpart_filter(self) -> AllplanIFW.ElementSelectFilterSetting:
        """Property with a selection filter accepting only PythonParts

        Returns:
            Selection filter
        """
        type_uuids = [AllplanIFW.QueryTypeID(AllplanElementAdapter.PythonPart_TypeUUID)]
        selection_query = AllplanIFW.SelectionQuery(type_uuids)
        return AllplanIFW.ElementSelectFilterSetting(selection_query, False)

    @property
    def input_mode(self) -> FixturePlacementInteractor.InputMode:
        """Property for the current input mode.

        Setting to MOVE initializes coordinate input
        Setting to PLACE shows the VS-Palette palette and initializes coordinate input
        Setting to SELECT shows the main palette and removes the VS-Palette or resets PythonPart to move

        Returns:
            Current input mode

        Raises:
            ValueError: when by switching to PLACEMENT the path to VS-pythonpart is invalid
        """
        return self.__input_mode

    @input_mode.setter
    def input_mode(self, value: FixturePlacementInteractor.InputMode):
        # by changing the mode to selection, close VS palette and show default palette
        if value == self.InputMode.SELECT:
            if self.visual_script_service is not None:
                self.visual_script_service = None
                self.build_ele.FixtureFilePath.value = ""
                self.main_palette_service.refresh_palette(self.build_ele_list, self.control_props_list)
                self.main_palette_service.update_palette(-1, True)

            elif self.input_mode == self.InputMode.MOVE:
                AllplanIFW.VisibleService.ShowAllElements()

            self.selected_pythonpart = AllplanBasisElements.MacroPlacementElement()

            prompt_msg = AllplanIFW.InputStringConvert("Select a VS-PythonPart from library or pick one from the model")
            self.coord_input.InitFirstElementInput(prompt_msg)
            self.coord_input.SetElementFilter(self.pythonpart_filter)

        elif value == self.InputMode.PLACE:
            if not (vs_pythonpart_path := self.build_ele.FixtureFilePath.value).endswith(".pyp"):
                raise ValueError(f"The path to the VS-PythonPart is invalid: {vs_pythonpart_path}]")

            self.main_palette_service.close_palette()
            self.visual_script_service = VisualScriptService(self.coord_input,
                                                             vs_pythonpart_path,
                                                             self.str_table_service,
                                                             self.build_ele_list,
                                                             self.control_props_list,
                                                             [])
            self.init_placement_coord_input()
        else:
            self.init_placement_coord_input()

        self.__input_mode = value

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

    def on_value_input_control_enter(self) -> bool:
        """Handles the event of hitting enter during the input in the edit field in the dialog line

        Returns:
            True in any case
        """
        return True

    def modify_element_property(self, page: int, name: str, value: Any):
        """Called after every property modification in the property pallette

        Args:
            page:   page of the property
            name:   name of the property
            value:  new value for property
        """
        if name == "SnapByRadioGroup" and value != "SnapByPoint":
            AllplanIFW.HighlightService.CancelAllHighlightedElements(self.coord_input.GetInputViewDocumentID())

        # in placement mode, pass the argument to the visual script service
        if self.input_mode == self.InputMode.PLACE and self.visual_script_service is not None:
            self.visual_script_service.modify_element_property(page, name, value)
        else:
            if self.main_palette_service.modify_element_property(page, name, value):
                self.main_palette_service.update_palette(-1, False)

    def on_control_event(self, event_id: int):
        """ Handles the on control event

        This method just passes the event_id to the loaded VS-PythonPart, if loaded

        Args:
            event_id: event id of button control.
        """
        if self.input_mode == self.InputMode.PLACE and self.visual_script_service is not None:
            self.visual_script_service.on_control_event(event_id)

    def on_mouse_leave(self):
        """ Handles the event of mouse leaving the viewport window.

        The preview is drawn on the last known mouse position.
        """
        self.on_preview_draw()

    def set_active_palette_page_index(self, active_page_index: int):
        """ Handles the event of changing the page in the property palette and a dialog
        (e.g. open file dialog) being closed.

        Switches to PLACE mode directly after selecting a VS-PythonPart

        Args:
            active_page_index: index of the active page, starting from 0
        """
        fixture_path = self.build_ele.FixtureFilePath.value # type: ignore

        if active_page_index == 0 and fixture_path.endswith(".pyp") and self.input_mode == self.InputMode.SELECT:
            self.input_mode = self.InputMode.PLACE

    def on_cancel_function(self) -> bool:
        """Handles the event of hitting ESC during the input.

        When in PLACE mode, passes the event to VS-PythonPart. When true is received, switches
        to SELECT mode. Otherwise input continues.
        When in MOVE mode, switches to SELECT.
        When in SELECT mode, terminates the PythonPart.

        Returns:
            True when should be terminated, False when it should still run.
        """
        if self.input_mode in [self.InputMode.PLACE, self.InputMode.MOVE]:
            if self.visual_script_service is not None:
                vs_on_cancel_result = self.visual_script_service.on_cancel_function()
                if not vs_on_cancel_result:
                    return False
            self.input_mode = self.InputMode.SELECT
            return False

        self.main_palette_service.close_palette()
        return True

    def on_cancel_by_menu_function(self):
        """ Called when the user has started another menu function during the runtime of
        the PythonPart.

        All the palettes are closed and the PythonPart is terminated.
        """
        if self.input_mode == self.InputMode.PLACE and self.visual_script_service is not None:
            self.visual_script_service.close_all()

        self.main_palette_service.close_palette()

    def process_mouse_msg(self,
                          mouse_msg: int,
                          pnt      : AllplanGeo.Point2D,
                          msg_info : AllplanIFW.AddMsgInfo) -> bool:
        """Handles the mouse message event (mouse move, click, etc...)

        -   In SELECT mode, element search is performed (a PythonPart is searched).
        -   In PLACE and MOVE mode, point search is performed.

        When mouse click is detected, then...
        -   In SELECT mode, selects the element (if found) and switches to MOVE mode
        -   In MOVE mode, moves the picked PythonPart to a new position and switches to SELECT mode
        -   In PLACE mode, creates the VS-PythonPart. Does not changes the mode.

        Args:
            mouse_msg:  the mouse message.
            pnt:        the input point in view coordinates
            msg_info:   additional message info.

        Returns:
            True
        """

        # do nothing, if no fixture specified
        if self.input_mode == self.InputMode.SELECT:
            ele_found = self.coord_input.SelectElement(mouse_msg, pnt, msg_info,
                                                       True, False, False)
        else:
            self.placement_point = self.coord_input.GetInputPoint(mouse_msg,
                                                                  pnt,
                                                                  msg_info,
                                                                  self.trace_pnt,
                                                                  self.input_mode == self.InputMode.MOVE).GetPoint()


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
            if self.input_mode == self.InputMode.SELECT and ele_found:
                self.pick_up_pythonpart()
                self.input_mode = self.InputMode.MOVE

            elif self.input_mode in [self.InputMode.PLACE, self.InputMode.MOVE]:
                self.create_elements()
                if self.input_mode == self.InputMode.MOVE:
                    self.input_mode = self.InputMode.SELECT
        return True

    def pick_up_pythonpart(self):
        """Pick up selected PythonPart.

        -   Get MacroPlacement from selected PythonPart
        -   Reset its placement matrix
        -   Save it in the appropriate attribute
        -   Hide the original one
        """
        # get python object
        pythonpart_adapter       = self.coord_input.GetSelectedElements()
        self.selected_pythonpart = cast(AllplanBasisElements.MacroPlacementElement,
                                        AllplanBaseElements.GetElements(pythonpart_adapter)[0])
        # reset the placement matrix
        placement_props        = self.selected_pythonpart.MacroPlacementProperties
        translation_vec        = placement_props.Matrix.GetTranslationVector()
        self.trace_pnt         = AllplanGeo.Point3D(translation_vec.X, translation_vec.Y, translation_vec.Z)
        placement_props.Matrix = AllplanGeo.Matrix3D()

        self.selected_pythonpart.SetMacroPlacementProperties(placement_props)

        # hide the original
        AllplanIFW.VisibleService.ShowElements(pythonpart_adapter, False)

    def create_elements(self):
        """Create the elements in the database by executing a PythonPart transaction

        In PLACE mode creates the VS-PythonPart using VisualScriptService
        In MOVE mode modifies (moves) the selected PythonPart
        """
        if self.input_mode == self.InputMode.PLACE and self.visual_script_service is not None:
            elements_to_create = self.visual_script_service.create_pythonpart(AllplanGeo.Matrix3D(),
                                                                              AllplanGeo.Matrix3D())

        elif self.input_mode == self.InputMode.MOVE:
            elements_to_create = [self.selected_pythonpart]

        else:
            return

        pyp_transaction = PythonPartTransaction(self.doc)
        pyp_transaction.execute(self.placement_matrix,
                                self.coord_input.GetViewWorldProjection(),
                                elements_to_create,
                                ModificationElementList())

    def init_placement_coord_input(self):
        """Initialize the coordinate input

        The input is initialized with an edit control for angle input. The angle is used to rotate
        the fixture around its local Z axis
        """

        prompt = AllplanIFW.InputStringConvert("Place the PythonPart; rotation around Z axis:")

        input_control = AllplanIFW.ValueInputControlData(AllplanIFW.eValueInputControlType.eANGLE_COMBOBOX,
                                                         initValue     = 0,
                                                         minValue      = -3.14590,
                                                         maxValue      = 3.1459,
                                                         bSetFocus     = True,
                                                         bDisableCoord = False)

        self.coord_input.InitFirstPointValueInput(prompt, input_control)

    def draw_preview(self):
        """Draw the element preview in the viewport using current values for the placement point,
        normal vector and additional rotation"""

        if self.input_mode == self.InputMode.PLACE and self.visual_script_service is not None:
            AllplanBaseElements.DrawElementPreview(self.doc,
                                                   self.placement_matrix,
                                                   self.visual_script_service.get_preview_elements(),
                                                   bDirectDraw  = False,    # FIXME: preview is not shown in the UVS
                                                   assoRefObj   = None)
        elif self.input_mode == self.InputMode.MOVE:
            AllplanBaseElements.DrawElementPreview(self.doc,
                                                   self.placement_matrix,
                                                   [self.selected_pythonpart],
                                                   bDirectDraw  = False,    # FIXME: preview is not shown in the UVS
                                                   assoRefObj   = None)
