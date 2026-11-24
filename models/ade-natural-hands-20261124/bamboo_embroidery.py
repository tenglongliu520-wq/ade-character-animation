"""Place shallow bamboo embroidery on the front of the inner robe."""
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

def add_bamboo(garment, material, mesh, curve):
    thread=material("Bamboo embroidery stem","769b8e",.83)
    leaf_mat=[material("Bamboo embroidery jade","83a596",.81),material("Bamboo embroidery pale jade","a0bbac",.81)]
    bpy.context.view_layer.update()
    surface=BVHTree.FromObject(garment,bpy.context.evaluated_depsgraph_get())
    def point(x,z,depth):
        hit,_,_,_=surface.ray_cast(Vector((x,-1,z)),Vector((0,1,0)))
        if hit is None:
            raise ValueError(f"Bamboo outside robe: {x}, {z}")
        return x,hit.y-depth,z
    def twig(name,positions,radius):
        curve("Bamboo embroidery "+name,[point(x,z,.0018) for x,z in positions],radius,thread)
    def leaf(name,start,end,width,shade):
        start,end=Vector(start),Vector(end)
        axis=end-start
        side=Vector((-axis.y,axis.x)).normalized()
        vertices=[]
        for t,spread in ((0,.06),(.17,.56),(.42,1),(.69,.69),(1,.03)):
            middle=start.lerp(end,t)+side*width*.32*(4*t*(1-t))
            for column,depth in ((-1,.0018),(0,.0038),(1,.0018)):
                position=middle+side*width*spread*column
                vertices.append(point(position.x,position.y,depth))
        faces=[(i,i+3,i+4,i+1) for row in range(4) for col in range(2) for i in (3*row+col,)]
        mesh("Bamboo embroidery "+name,vertices,faces,leaf_mat[shade])
    twig("lower culm",[(-.094,.326),(-.089,.390),(-.081,.461),(-.075,.534),(-.069,.596),(-.060,.672)],.0022)
    twig("lower left twig",[(-.082,.451),(-.111,.481),(-.137,.506)],.00125)
    twig("lower right twig",[(-.075,.527),(-.053,.551),(-.026,.574)],.0013)
    twig("lower crown",[(-.068,.586),(-.087,.616),(-.101,.635)],.00125)
    for i,(x,z) in enumerate(((-.089,.390),(-.081,.457),(-.075,.526),(-.069,.592))):
        twig(f"lower culm node {i+1}",[(x-.004,z-.001),(x+.004,z+.001)],.0018)
    twig("chest stem",[(.033,1.093),(.048,1.126),(.059,1.168)],.00155)
    leaves=[
        ((-.111,.481),(-.157,.488),.009,0),((-.126,.496),(-.153,.537),.008,1),((-.107,.477),(-.142,.453),.008,1),
        ((-.051,.553),(-.008,.559),.009,1),((-.032,.568),(.001,.612),.009,0),((-.047,.556),(-.013,.532),.008,1),
        ((-.084,.612),(-.121,.645),.008,0),((-.095,.626),(-.114,.676),.007,1),((-.065,.635),(-.030,.668),.008,1),
        ((-.060,.665),(-.051,.710),.006,0),((.045,1.122),(.018,1.154),.0057,1),((.052,1.136),(.083,1.151),.0059,0),
        ((.058,1.157),(.067,1.193),.0051,1),
    ]
    for i,spec in enumerate(leaves):
        leaf(f"leaf {i+1}",*spec)
