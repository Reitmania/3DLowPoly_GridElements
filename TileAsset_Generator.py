import bpy 
import bmesh

from mathutils import Vector, Matrix
from random import random, seed, uniform, randint, randrange

HEIGHT = 3
WIDTH = 1
RANGE_HEIGHT = .5
RANGE_OFFSET_IN = .15



'''
# Deselect all
bpy.ops.object.select_all(action='DESELECT')

# https://wiki.blender.org/wiki/Reference/Release_Notes/2.80/Python_API/Scene_and_Object_API
bpy.data.objects['Cube'].select_set(True) # Blender 2.8x

bpy.ops.object.delete() 



context = bpy.context

bpy.ops.mesh.primitive_plane_add(
        enter_editmode=True)
ob = context.object
me = ob.data
bm = bmesh.from_edit_mesh(me)
for i, v in enumerate(bm.verts):
    v.select_set(not i)


#bm.select_mode |= {'VERT'}
#bm.select_flush_mode()
    
#bmesh.update_edit_mesh(me)
'''

def reset_scene():
    # Deselect all
    bpy.ops.object.select_all(action='DESELECT')

    # https://wiki.blender.org/wiki/Reference/Release_Notes/2.80/Python_API/Scene_and_Object_API
    bpy.data.objects['Cube'].select_set(True) # Blender 2.8x

    bpy.ops.object.delete() 

def generate_inside(v2,v3,bm, leftside, rightside):
    def create_step(va,vb):
        tmp_height = uniform(.05, RANGE_HEIGHT)
        tmp_offset = uniform(-RANGE_OFFSET_IN, RANGE_OFFSET_IN)
        while(va.co[1]+tmp_offset > 0 or va.co[1]+tmp_offset < (-WIDTH/2)):
            tmp_offset = uniform(-RANGE_OFFSET_IN, RANGE_OFFSET_IN)
        vc = bm.verts.new((va.co[0],va.co[1]+tmp_offset,va.co[2] + tmp_height))
        vd = bm.verts.new((vb.co[0],vb.co[1]+tmp_offset,vb.co[2] + tmp_height))
        bm.faces.new((va, vb, vd, vc))
        return vb.co[2] + tmp_height, vc, vd

    starty = v2.co[1] #v2 - right, v3 - left
    #first step, starting with v2 and v3
    cur_height, v2, v3 = create_step(v2,v3)
    rightside.append(v2)
    leftside.append(v3)

    while cur_height + RANGE_HEIGHT < HEIGHT:
        cur_height, v2, v3 = create_step(v2,v3)
        rightside.append(v2)
        leftside.append(v3)

    #last step
    vc = bm.verts.new((v2.co[0],starty,HEIGHT))
    vd = bm.verts.new((v3.co[0],starty,HEIGHT))
    bm.faces.new((v2, v3, vd, vc))
    return vc, vd, leftside, rightside

def generate_outside(va,vb,bm,mode, leftside, rightside):
    starty = va.co[1]
    if(mode == 0): #normal
        vc = bm.verts.new((va.co[0],va.co[1],HEIGHT))
        vd = bm.verts.new((vb.co[0],vb.co[1],HEIGHT))
        bm.faces.new((va, vb, vd, vc))
    elif(mode == 1): #down
        #first step, starting with v2 and v3
        #cur_height, v2, v3 = create_step(v2,v3)
        tmp_height = uniform(.05, RANGE_HEIGHT)
        tmp_offset = uniform(-RANGE_OFFSET_IN, RANGE_OFFSET_IN)
        while(va.co[1]+tmp_offset < 0 or va.co[1]+tmp_offset > (WIDTH/2)):
            tmp_offset = uniform(-RANGE_OFFSET_IN, RANGE_OFFSET_IN)
        vc = bm.verts.new((va.co[0],va.co[1]+tmp_offset,va.co[2] + tmp_height))
        vd = bm.verts.new((vb.co[0],vb.co[1]+tmp_offset,vb.co[2] + tmp_height))
        bm.faces.new((va, vb, vd, vc))
    return vc,vd, leftside, rightside
   

def extrude_face(bm, face, translate_forwards=0.0, extruded_face_list=None):
    new_faces = bmesh.ops.extrude_discrete_faces(bm, faces=[face])['faces']
    if extruded_face_list != None:
        extruded_face_list += new_faces[:]
    new_face = new_faces[0]
    bmesh.ops.translate(bm,
                        vec=new_face.normal * translate_forwards,
                        verts=new_face.verts)
    return new_face

def generate_asset():
    # and here comes the magic

    obj = bpy.context.object
    #me = obj.data
    #bm = bmesh.from_edit_mesh(me)
    bm = bmesh.new()
    #bmesh.ops.create_cube(bm, size=1)

    mode = 0 # 0 - normal, 1 - down, 2 - up

    if(mode == 0):
        # ground plate normal
        x1 = WIDTH/2
        x2 = -WIDTH/2
        y1 = WIDTH/2
        y2 = -WIDTH/2
    elif(mode == 1):
        x1 = WIDTH/2
        x2 = -WIDTH/2
        y1 = 0
        y2 = -WIDTH/2

    v1 = bm.verts.new((x1,y1,0.0)) #back right
    v2 = bm.verts.new((x1,y2, 0.0)) # front right
    v3 = bm.verts.new((x2, y2, 0.0)) # front left
    v4 = bm.verts.new((x2, y1, 0.0)) # back left
    bm.faces.new((v1, v2, v3, v4))

    leftside = list()
    rightside = list()
    rightside.append(v1)
    rightside.append(v2)
    leftside.append(v4)
    leftside.append(v3)

    vo1,vo2, leftside, rightside = generate_inside(v2,v3,bm, leftside, rightside)    
    vo3,vo4, leftside, rightside = generate_outside(v1,v4,bm,mode, leftside, rightside)

    rightside.append(vo1)
    rightside.append(vo3)
    leftside.append(vo2)
    leftside.append(vo4)    

    #deckel druff
    bm.faces.new((vo1, vo2, vo4, vo3))
    #seiten dran
    bm.faces.new(rightside)
    bm.faces.new(leftside)






    # Finish up, write the bmesh into a new mesh
    me = bpy.data.meshes.new('Mesh')
    bm.to_mesh(me)
    bm.free()

    # Add the mesh to the scene
    scene = bpy.context.scene
    obj = bpy.data.objects.new('Asset', me)
    # scene.objects.link(obj)
    scene.collection.objects.link(obj)

    # This is optional, you could also stay in editmode.
    #bpy.ops.object.mode_set(mode='OBJECT')

    '''
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1)
    scale_vector = Vector((WIDTH,WIDTH,HEIGHT))
    #scale_vector = Vector((uniform(0.75, 2.0), uniform(0.75, 2.0), uniform(0.75, 2.0)))
    bmesh.ops.scale(bm, vec=scale_vector, verts=bm.verts)

    list_faces = bm.faces 
    print(list_faces[0])

    for face in bm.faces[:]:
        face = extrude_face(bm, face, 0.25)

    # Finish up, write the bmesh into a new mesh
    me = bpy.data.meshes.new('Mesh')
    bm.to_mesh(me)
    bm.free()

    # Add the mesh to the scene
    scene = bpy.context.scene
    obj = bpy.data.objects.new('Asset', me)
    # scene.objects.link(obj)
    scene.collection.objects.link(obj)

    # Select and make active
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)

    # scene.objects.active = obj
    # obj.select = True

    # Recenter the object to its center of mass
    bpy.ops.object.origin_set(type='ORIGIN_CENTER_OF_MASS')
    ob = bpy.context.object
    ob.location = (0, 0, 0)
    '''

def generate_backplate():
    bpy.ops.mesh.primitive_plane_add(size=2, enter_editmode=False, align='WORLD', location=(0, 0, 0), rotation=(0, 0, 0))
    obj = bpy.data.objects["Plane"]
    #select vertex
    obj = bpy.context.active_object
    bpy.ops.object.mode_set(mode = 'EDIT') 
    bpy.ops.mesh.select_mode(type="FACE")
    bpy.ops.mesh.subdivide(number_cuts=3)
    bpy.ops.discombobulate.ops()


    # add greeble

if __name__ == "__main__":
    # lets build some assets for PBD

    start_generator = True
    
    if start_generator:
        reset_scene()
        obj = generate_asset()
        generate_backplate()


