Pseudonuclear 3d simulator
- python tkinter used
- opengl 4.3 with compute shader used for parallel computation

for use install libraries:
- python -m pip install pillow numpy pyglm pyopengl pyopengltk

Tested on:
- integrated Intel Iris Xe Graphics

Controls:
-    Mouse + click -  rotate camera
-    Mouse + shift + click  - move camera
-    Mouse wheel - move camera forward and back

 In merge mode (adding nucleons or files):
- enter or double-click - do merge 
- mouse wheel - change parameter
- mouse wheel + shift - slow change
- mouse wheel + control - move camera forward and back
- g - move,  x,y,z for select axis
- r - rotate object, x,y,z for select rotate axis

1. selection mode
    double-click an nucleon, then use the mouse wheel to add neighboring nucleons to the selection
    ctrl + double-click  - append/remove to/from selection
    enter or middle-button or double-click on selection - go to merge mode with selected nucleons
    also "r" and "g" - go to merge mode with move and rotation
    <delete> - delete selected
    ctrl + alt + s - save selected nucleons

Do not view video parallel to use this simulator, the simulation may hang


Some examples:

!["demopic 1](images/demo1.PNG?raw=true )
!["demopic 2](images/demo2.PNG?raw=true )

