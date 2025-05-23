# Fixture placement

This is an extension (PythonPart) for ALLPLAN, that can speed-up placing fixtures in the model
by aligning them with the curved surface of the architectural elements, such as
circular walls.

![Placement GIF](./docs/assets/Placement.gif)

## Installation

1.  Download the `.allep` package from the [release page](https://github.com/bmarciniec/fixture-placement/releases).
2.  Install it in ALLPLAN via drag&drop

> [!IMPORTANT]
> For ALLPLAN 2025, make sure to download the right release, e.g. _2025.X.X_

The plugin contains one PythonPart _Fixture placement_. It can be run from the ALLPLAN Library:

_Private_ -> AllepPlugins -> _AllplanGmbH_ -> FixturePlacement -> Fixture placement

## Features

-   _Fixture placement_ allows you to place small components (like fixtures)
    created as PythonParts using VisualScripting
-   The component follows your mouse, like during regular placement, but
    when you point on any 3D volume geometry (e.g. a wall), it is rotated
    so that its aligned with the solid's surface
-   You can rotate the component around it's local Z axis by specifying an
    angle in the dialog line (on the bottom-left corner)
-   The alignment works also in a UVS
-   The tool allows you to **place new and move existing** PythonParts.

## How to use

1.  After starting the _Fixture placement_ select the **snapping mode** you want to use:

    *   _By ray_ (recommended): a ray is sent from the observer eye in the direction
        pointed by the mouse. The component is placed at the intersection point
        of the ray and **the face of any 3D volume, it hits first**. The component
        is also aligned with the normal vector of this face.
    *   _By point_:as soon as a point has been detected by the ALLPLAN Point Snapping
        functionality (which is indicated by a red cross) the **face nearest to this point**
        is taken as reference. The component is placed at this point and aligned with the
        nearest face.

2.  To **place a new** VisualScripting PythonPart, click on _Browse..._ and select
    the `.pyp` file.

3.  To **move an existing** PythonPart (not necessarily VisualScripting), pick it
    by clicking on it in the viewport

## Things to keep in mind

-   You can only place PythonParts created using VisualScripting.
-   The tool aligns local **Z axis** of the component with the normal vector of the
    surface - you cannot change that behavior.
-   The tool is not capable of snapping to objects with B-Rep geometry (in ALLPLAN known
    as _general 3D objects_)

## Wishes & Bugs

To report a bug or a wish, [open an issue](https://github.com/bmarciniec/fixture-placement/issues/new)
(requires a GitHub account) or let us know at <pythonparts@allplan.com>.
