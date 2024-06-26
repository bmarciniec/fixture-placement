"""Module containing implementation of a snapping functionality """
import typing

import NemAll_Python_BaseElements as AllplanBaseElements
import NemAll_Python_Geometry as AllplanGeo
import NemAll_Python_IFW_ElementAdapter as AllplanElementAdapter
import NemAll_Python_IFW_Input as AllplanIFW


class SnapToSolid():
    """Implementation of snapping to a solid.

    Snapping to a solid is a feature, that extends the classic object placement functionality
    in Allplan. This class contains methods to calculate placement matrix that will snap a geometry
    object to a solid by identifying a point on this solid, identify a face and a point on this face.
    This matrix can then be used to place an object on this face and align with its normal vector.

    Remarks:
        The snapping works only for objects with polyhedron geometry.
        Currently no support for BReps!

    Attributes:
        _polyhedron:    reference polyhedron to snap to
        _normal_vector: normal vector of the face, to which the snapping will be done
        _coord_input:   object representing coordinate input in Allplan viewport
        _filter:        filter to pick up objects valid for snapping
    """

    def __init__(self,
                 coord_input: AllplanIFW.CoordinateInput):
        """Default constructor

        Args:
            coord_input:  object representing coordinate input in Allplan viewport
        """
        # set initial values of private properties
        self._polyhedron  = AllplanGeo.Polyhedron3D()
        self._ref_element = AllplanElementAdapter.BaseElementAdapter()
        self._coord_input = coord_input
        self._normal_vec  = AllplanGeo.Vector3D(0, 0, 1)

        # set up a filter
        class ElementFilter():
            """ Implementation of a filter accepts only model elements with a polyhedron geometry"""

            def __call__(self, element: AllplanElementAdapter.BaseElementAdapter) -> bool:
                """ Execute the filtering

                Args:
                    element: element to filter

                Returns:
                    True, when element's geometry is a polyhedron
                """

                return all([isinstance(element.GetModelGeometry(), AllplanGeo.Polyhedron3D),
                           element != AllplanElementAdapter.ClippingPathBody_TypeUUID])

        selection_query   = AllplanIFW.SelectionQuery([ElementFilter()])
        self._filter = AllplanIFW.ElementSelectFilterSetting(filter            = selection_query,
                                                             bSnoopAllElements = False)

    @property
    def reference_element(self) -> AllplanElementAdapter.BaseElementAdapter:
        return self._ref_element

    def _find_nearest_face(self, polyhedron: AllplanGeo.Polyhedron3D, point: AllplanGeo.Point3D) -> tuple[int, float]:
        """Finds the face of a given polyhedron, whose plane is closest to the given point

        Args:
            polyhedron: polyhedron to inspect
            point:      point in 3D space

        Returns:
            index of the face, whose plane is nearest to the given point
            distance between the point and this face

        Raises:
            ValueError: is the given polyhedron has more than 2^14 faces
        """

        if (faces_count := polyhedron.GetFacesCount()) > 2 ** 14:
            raise ValueError("The polyhedron is too complex")

        distances: list[float] = []

        for face_index in range(faces_count):
            _, face_nv         = polyhedron.GetNormalVectorOfFace(face_index)
            _, edge            = polyhedron.GetFace(face_index).GetEdge(0)
            _, face_vertex, _  = polyhedron.GetEdgeVertices(edge)

            # distance between face's plane and the point
            distance = abs(face_nv.DotProduct(AllplanGeo.Vector3D(point - face_vertex)))
            distances.append(distance)

        min_distance = min(distances)
        return distances.index(min_distance), min_distance

    @staticmethod
    def _calc_placement_matrix(normal_vec   : AllplanGeo.Vector3D,
                               placement_pnt: AllplanGeo.Point3D,
                               z_rotation   : AllplanGeo.Angle = AllplanGeo.Angle()) -> AllplanGeo.Matrix3D:
        """Calculates a placement matrix

        A placement matrix is a 4x4 transformation matrix, that is supposed to transform the snapped
        element from its local coordinate system to the global coordinate system, by:

        -   translating from local origin point (0,0,0) to global placement point
        -   rotating the object in space in a way, that:

            *   its local Z+ axis is aligned with the given normal vector
            *   its local X axis remains on the global XY plane after the rotation, if no additional
                rotation around the local Z axis is given (z_rotation)

        The final placement matrix results from following transformations:

        1.  Rotation:       rotate the object around local Z to align local X axis with the projection
                            of the normal vector onto the XY plane
        2.  Rotation:       (optional) rotate the object around local Z axis by angle z_rotation (if specified)
        3.  Rotation:       align the local Z axis with the normal vector
        4.  Translation:    from local (0,0,0) to global point specified placement_pnt

        Args:
            normal_vec:     normal vector to align the local Z axis to
            placement_pnt:  point to translate the geometry into in the 4th step
            z_rotation:     additional rotation around local Z-axis for 2nd step

        Returns:
            Placement matrix
        """
        # step 1
        project_on_xy = AllplanGeo.Matrix3D(1, 0, 0, 0,
                                            0, 1, 0, 0,
                                            0, 0, 0, 0,
                                            0, 0, 0, 1)
        normal_vec_xy = normal_vec * project_on_xy

        pre_rotate = AllplanGeo.Matrix3D()

        if not normal_vec_xy.IsZero():
            pre_rotate.SetRotation(AllplanGeo.Vector3D(1, 0, 0) , normal_vec_xy)

        # step 2
        pre_rotate.Rotation(AllplanGeo.Line3D(0, 0, 0,
                                              0, 0, 1),
                            z_rotation)
        # step 3
        align_with_nv = AllplanGeo.Matrix3D()
        align_with_nv.SetRotation(AllplanGeo.Vector3D(0, 0, 1),
                                  normal_vec * -1)
        # step 4
        translate_to_global = AllplanGeo.Matrix3D()
        translate_to_global.SetTranslation(AllplanGeo.Vector3D(placement_pnt))

        # combining steps:
        #         1 + 2          3                 4
        return pre_rotate * align_with_nv * translate_to_global

    @typing.overload
    def snap_by_ray(self,
                    input_pnt  : AllplanGeo.Point3D,
                    rotation   : AllplanGeo.Angle,
                    mouse_msg  : int,
                    msg_info   : AllplanIFW.AddMsgInfo,
                    ) -> AllplanGeo.Matrix3D:
        """Calculates placement matrix, that snaps to an element with polyhedron geometry.

        This method search for a face on a polyhedron by sending a ray from the observer eye
        in the direction of the view. The first face, this ray hits, is considered as found.
        The resulting placement matrix will align the snapped object with the found face
        AND translate the object onto this face. If no face is found, the resulting placement
        matrix will align (rotate) the object with the last known face, but no translation
        will be performed.

        Args:
            input_pnt:  input point in world coordinate system
            rotation:   rotation around local Z axis
            mouse_msg:  mouse message
            msg_info:   additional message info

        Returns:
            placement matrix

        Remarks:
            Use this variant inside an event that is triggered by a mouse move, i.e. where
            the mouse_msg is sent.
        """

    @typing.overload
    def snap_by_ray(self,
                    input_pnt  : AllplanGeo.Point3D,
                    rotation   : AllplanGeo.Angle,
                    ) -> AllplanGeo.Matrix3D:
        """Actual implementation

        Args:
            input_pnt:  input point in world coordinate system
            rotation:   rotation around local Z axis
            mouse_msg:  mouse message
            msg_info:   additional message info

        Returns:
            placement matrix

        Remarks:
            Use this variant inside an event that is NOT triggered by a mouse move, e.g.,
            on_preview_draw (triggered by input in the dialog line)
        """

    def snap_by_ray(self,
                    input_pnt  : AllplanGeo.Point3D,
                    rotation   : AllplanGeo.Angle,
                    mouse_msg  : int = 512,
                    msg_info   : AllplanIFW.AddMsgInfo  = AllplanIFW.AddMsgInfo(),
                    ) -> AllplanGeo.Matrix3D:
        """Calculates placement matrix, that snaps to an element with polyhedron geometry.

        This method search for a face on a polyhedron by sending a ray from the observer eye
        in the direction of the view. The first face, this ray hits, is considered as found.
        The resulting placement matrix will align the snapped object with the found face
        AND translate the object onto this face. If no face is found, the resulting placement
        matrix will align (rotate) the object with the last known face, but no translation
        will be performed.

        Args:
            input_pnt:  input point in world coordinate system
            rotation:   rotation around local Z axis
            mouse_msg:  mouse message
            msg_info:   additional message info

        Returns:
            placement matrix
        """
        view_world_proj  = self._coord_input.GetViewWorldProjection()
        face_detected    = False
        view_pnt         = view_world_proj.WorldToView(input_pnt)                   # convert input point from world to view coordinates
        element_detected = self._coord_input.SelectElement(mouse_msg, view_pnt, msg_info,
                                                           False, True, False,
                                                           self._filter)
        if not element_detected:
            self._ref_element = AllplanElementAdapter.BaseElementAdapter()
            return self._calc_placement_matrix(normal_vec    = self._normal_vec,    # align with last known normal vector
                                               placement_pnt = input_pnt,           # place in the given point, no translation
                                               z_rotation    = rotation)

        self._ref_element = self._coord_input.GetSelectedElement()

        face_detected, _, intersection_ray = \
            AllplanBaseElements.FaceSelectService.SelectPolyhedronFace(self._ref_element,
                                                                       view_pnt,
                                                                       True,
                                                                       view_world_proj,
                                                                       self._coord_input.GetInputViewDocument(),
                                                                       True)
        if face_detected:
            self._normal_vec = intersection_ray.FaceNv          # overwrite the last known normal vector
            placement_pnt = intersection_ray.IntersectionPoint  # place ON the detected face
        else:
            placement_pnt = input_pnt                           # place in the given point, no translation

        return self._calc_placement_matrix(normal_vec    = self._normal_vec,
                                           placement_pnt = placement_pnt,
                                           z_rotation    = rotation)

    @typing.overload
    def snap_by_point(self,
                      input_pnt : AllplanGeo.Point3D,
                      rotation  : AllplanGeo.Angle,
                      tolerance : float = 20.0) -> AllplanGeo.Matrix3D:
        """ Snap to the face of the reference element, that is nearest to the defined point.

        Args:
            input_pnt:      input point in world coordinate system
            rotation:       rotation around local Z axis
            mouse_msg:      mouse message
            view_pnt:       input point in view coordinate system
            msg_info:       additional message info
            tolerance:      if the distance between the point and the nearest face is larger than
                            this value, no snapping is performed

        Returns:
            normal vector of the polygon face, where the point was found

        Remarks:
            Use this variant inside an event that is NOT triggered by a mouse move, e.g.,
            on_preview_draw (triggered by input in the dialog line)
        """
    @typing.overload
    def snap_by_point(self,
                      input_pnt : AllplanGeo.Point3D,
                      rotation  : AllplanGeo.Angle,
                      mouse_msg : int,
                      view_pnt  : AllplanGeo.Point2D,
                      msg_info  : AllplanIFW.AddMsgInfo,
                      tolerance : float = 20.0) -> AllplanGeo.Matrix3D:
        """ Snap to the face of the reference element, that is nearest to the defined point.

        Args:
            input_pnt:      input point in world coordinate system
            rotation:       rotation around local Z axis
            mouse_msg:      mouse message
            view_pnt:       input point in view coordinate system
            msg_info:       additional message info
            tolerance:      if the distance between the point and the nearest face is larger than
                            this value, no snapping is performed

        Returns:
            normal vector of the polygon face, where the point was found

        Remarks:
            Use this variant inside an event that is triggered by a mouse move, i.e. where
            the mouse_msg is sent.
        """

    def snap_by_point(self,
                      input_pnt : AllplanGeo.Point3D,
                      rotation  : AllplanGeo.Angle,
                      mouse_msg : int                   = 512,
                      view_pnt  : AllplanGeo.Point2D    = AllplanGeo.Point2D(),
                      msg_info  : AllplanIFW.AddMsgInfo = AllplanIFW.AddMsgInfo(),
                      tolerance : float                 = 20.0) -> AllplanGeo.Matrix3D:
        """ Snap to the face of the reference element, that is nearest to the defined point.

        Args:
            input_pnt:      input point in world coordinate system
            rotation:       rotation around local Z axis
            mouse_msg:      mouse message
            view_pnt:       input point in view coordinate system
            msg_info:       additional message info
            tolerance:      if the distance between the point and the nearest face is larger than
                            this value, no snapping is performed

        Returns:
            normal vector of the polyhedron face, where the point was found
        """
        # in case of mouse movement, search for element
        if view_pnt != AllplanGeo.Point2D():

            # if element is found, get it
            if self._coord_input.SelectGeometryElement(mouse_msg, view_pnt, msg_info, False):
                self._ref_element = self._coord_input.GetSelectedElement()

                # if found element has a valid polyhedron geometry, override the previous reference polyhedron
                if isinstance((phed := self._ref_element.GetModelGeometry()), AllplanGeo.Polyhedron3D) and phed.IsValid():
                    self._polyhedron = phed
                    AllplanIFW.HighlightService.HighlightElements(AllplanElementAdapter.BaseElementAdapterList([self._ref_element]))
            else:
                self._ref_element = AllplanElementAdapter.BaseElementAdapter()

        # perform snap, if there is a reference polyhedron to snap to
        if self._polyhedron != self._calc_placement_matrix(self._normal_vec, input_pnt, rotation):
            try:
                nearest_face_idx, distance_to_face = self._find_nearest_face(self._polyhedron, input_pnt)
            except ValueError:
                AllplanIFW.HighlightService.CancelAllHighlightedElements(self._coord_input.GetInputViewDocumentID())
                self._polyhedron = AllplanGeo.Polyhedron3D()
                return self._calc_placement_matrix(self._normal_vec, input_pnt, rotation)

            if distance_to_face <= tolerance:
                _, self._normal_vec = self._polyhedron.GetNormalVectorOfFace(nearest_face_idx)

        return self._calc_placement_matrix(self._normal_vec, input_pnt, rotation)
