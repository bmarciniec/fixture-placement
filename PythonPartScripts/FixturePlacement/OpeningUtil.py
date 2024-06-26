"""Module with utilities for creating openings and recesses"""

import NemAll_Python_ArchElements as AllplanArchElements
import NemAll_Python_Geometry as AllplanGeo
import NemAll_Python_IFW_ElementAdapter as AllplanElementAdapter

from TypeCollections.ModelEleList import ModelEleList


class OpeningUtil():
    """Utility class for creating opening elements"""
    @staticmethod
    def create_opening_in_wall(wall_element: AllplanElementAdapter.BaseElementAdapter,
                               placement_matrix: AllplanGeo.Matrix3D,
                               width: float,
                               depth: float,
                               height: float) -> ModelEleList:
        """Create a vertical, rectangular opening in a wall based on placement matrix and dimensions

        Args:
            wall_element:       reference to the wall, in which the opening is to be placed
            placement_matrix:   matrix describing the placement of the opening
            width:              opening width
            depth:              opening depth
            height:             opening height

        Raises:
            ValueError: if the wall_element does not point to a wall or if placement matrix does not place
                        the opening vertically

        Returns:
            list with one opening element
        """
        model_ele_list = ModelEleList()

        # check the element, where to create the opening
        if (ele_type := wall_element.GetElementAdapterType()).GetGuid() != AllplanElementAdapter.WallTier_TypeUUID:
            raise ValueError(f"Can only create opening in a wall, but {ele_type.DisplayName} was given")

        # in a wall, only a vertical opening can be created
        # check the normal vector of the opening, whether it lies in XY plane
        norm_vec = AllplanGeo.Vector3D(0,0,1) * placement_matrix
        if not AllplanGeo.Comparison.Equal(norm_vec.Z, 0.0, 1e-11):
            raise ValueError("Can only create a vertical openint")

        # calculate start and end point of the opening
        norm_vec = norm_vec.To2D
        adj_vec = norm_vec.Orthogonal()
        translation = placement_matrix.GetTranslationVector()
        start_point = AllplanGeo.Point2D() + translation.To2D - adj_vec * width/2
        end_point = AllplanGeo.Point2D() + translation.To2D + adj_vec * width/2

        # set opening properties
        opening_props = AllplanArchElements.GeneralOpeningProperties(AllplanArchElements.OpeningType.eNiche)

        opening_props.VisibleInViewSection3D   = True
        opening_props.Independent2DInteraction = False

        # set geometry properties of the opening
        opening_geo_props       = opening_props.GetGeometryProperties()
        opening_geo_props.Shape = AllplanArchElements.VerticalOpeningShapeType.eRectangle
        opening_geo_props.Depth = depth

        # disable the sill
        opening_sill_props      = opening_props.GetSillProperties()
        opening_sill_props.Type = AllplanArchElements.VerticalOpeningSillType.eNone

        # set opening bottom and top edge to absolute values
        opening_plane_refs                       = opening_props.PlaneReferences
        opening_plane_refs.TopPlaneDependency    = AllplanArchElements.PlaneReferences.PlaneReferenceDependency.eAbsElevation
        opening_plane_refs.BottomPlaneDependency = AllplanArchElements.PlaneReferences.PlaneReferenceDependency.eAbsElevation
        opening_plane_refs.BottomOffset          = translation.Z - height/2
        opening_plane_refs.TopOffset             = translation.Z + height/2
        opening_props.PlaneReferences            = opening_plane_refs

        opening_ele = AllplanArchElements.GeneralOpeningElement(opening_props, wall_element, start_point, end_point, False)
        model_ele_list.append(opening_ele)

        return model_ele_list
