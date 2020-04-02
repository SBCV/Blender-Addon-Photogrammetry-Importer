### Point Cloud Visualization and Rendering

Currently, this addon supports the following 3 point cloud visualization options:
* Representing the points with vertices of a Blender object (default)
* Draw the points with OpenGL 
* Representing the points with a Blender particle system (default)


![alt text](https://github.com/SBCV/Blender-Import-NVM-Addon/blob/master/doc/images/import_point_options.jpg)

Each option has different advantages / disadvantages.

### Representing the points with vertices of a Blender object

If selected, the addon adds a blender object with a vertex for each point in the point cloud. 

* Advantage: Low computational costs for visualization / rendering. 
* Disadvantage: Contains no color information.

### Representing the points with a particle system 

If selected, the point cloud is represented with two objects.
* One object associated with a particle system, which represents the structure of the point cloud. 
* One object that defines the shape of the particles.

The color of the particles is defined by a single material as shown in the image below.

![alt text](https://github.com/SBCV/Blender-Import-NVM-Addon/blob/master/doc/images/particle_system_material.jpg)
Note: The second input "Value" in the "Divide" node represents the number of particles in the point cloud.  

* Advantage: Contains color information, which can be rendered using Cycles. 
* Disadvantage: High computational costs for visualization / rendering, i.e. limited to medium-sized point clouds.

### Rendering the points with Opengl 
If selected, the point cloud is shown in the Viewport with OpenGL. That means, there is NO Blender object representing the points in the point cloud. The pose (i.e. rotation and translation) of the object can be changed by adjusting the corresponding "anchor" object.
* Advantage: Allows to show huge point clouds in the viewport - including color information. 
* Disadvantage: It is not possible to render these points (not even with OpenGL rendering). 
