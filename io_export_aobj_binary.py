bl_info = {
    "name": "Animated OBJ Format - Binary (.aobj)",
    "author": "Animated OBJ Community",
    "version": (2, 2, 0),
    "blender": (2, 80, 0),
    "location": "Object Properties > AOBJ Animation Sequences",
    "description": "Export mesh animations with pre-defined sequences",
    "category": "Import-Export",
}

import bpy
import struct
from bpy.props import StringProperty, BoolProperty, IntProperty, FloatProperty, CollectionProperty, PointerProperty
from bpy_extras.io_utils import ExportHelper

# Binary keyword identifiers
KW_GROUP = 1
KW_VERTEX = 2
KW_TEXCOORD = 3
KW_NORMAL = 4
KW_FACE = 5
KW_ANIM = 6
KW_FRAME = 7
KW_VDELTA = 8

class AnimSequenceItem(bpy.types.PropertyGroup):
    """Single animation sequence definition"""
    name: StringProperty(
        name="Name",
        description="Animation sequence name",
        default="Idle"
    )
    start_frame: IntProperty(
        name="Start",
        description="Start frame",
        default=0,
        min=0
    )
    end_frame: IntProperty(
        name="End",
        description="End frame (inclusive)",
        default=30,
        min=0
    )
    fps: IntProperty(
        name="FPS",
        description="Frames per second",
        default=30,
        min=1,
        max=255
    )

class AnimSequenceSettings(bpy.types.PropertyGroup):
    """Container for animation sequences on each object"""
    sequences: CollectionProperty(type=AnimSequenceItem)
    active_index: IntProperty()

# UI Panel in Object Properties
class AOBJ_PT_AnimSequences(bpy.types.Panel):
    bl_label = "AOBJ Animation Sequences"
    bl_idname = "AOBJ_PT_anim_sequences"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"
    
    @classmethod
    def poll(cls, context):
        return context.object and context.object.type == 'MESH'
    
    def draw(self, context):
        layout = self.layout
        obj = context.object
        
        if not hasattr(obj, "aobj_anim_settings"):
            layout.label(text="AOBJ settings not initialized")
            return
        
        settings = obj.aobj_anim_settings
        
        # List of sequences
        row = layout.row()
        row.template_list("AOBJ_UL_AnimSequences", "", settings, "sequences", 
                         settings, "active_index", rows=4)
        
        col = row.column(align=True)
        col.operator("aobj.add_sequence", icon='ADD', text="")
        col.operator("aobj.remove_sequence", icon='REMOVE', text="")
        col.separator()
        col.operator("aobj.move_sequence", icon='TRIA_UP', text="").direction = 'UP'
        col.operator("aobj.move_sequence", icon='TRIA_DOWN', text="").direction = 'DOWN'
        
        # Details of selected sequence
        if len(settings.sequences) > 0 and settings.active_index < len(settings.sequences):
            seq = settings.sequences[settings.active_index]
            box = layout.box()
            box.prop(seq, "name")
            box.prop(seq, "start_frame")
            box.prop(seq, "end_frame")
            box.prop(seq, "fps")

class AOBJ_UL_AnimSequences(bpy.types.UIList):
    """UI list for animation sequences"""
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            layout.label(text=item.name, icon='ANIM')
            layout.label(text=f"{item.start_frame}-{item.end_frame}")
        elif self.layout_type == 'GRID':
            layout.alignment = 'CENTER'
            layout.label(text=item.name)

class AOBJ_OT_AddSequence(bpy.types.Operator):
    bl_idname = "aobj.add_sequence"
    bl_label = "Add Animation Sequence"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        obj = context.object
        settings = obj.aobj_anim_settings
        
        item = settings.sequences.add()
        item.name = f"Anim_{len(settings.sequences)}"
        item.start_frame = context.scene.frame_start
        item.end_frame = context.scene.frame_end
        item.fps = context.scene.render.fps
        
        settings.active_index = len(settings.sequences) - 1
        return {'FINISHED'}

class AOBJ_OT_RemoveSequence(bpy.types.Operator):
    bl_idname = "aobj.remove_sequence"
    bl_label = "Remove Animation Sequence"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        obj = context.object
        settings = obj.aobj_anim_settings
        
        if len(settings.sequences) > 0:
            settings.sequences.remove(settings.active_index)
            settings.active_index = max(0, settings.active_index - 1)
        return {'FINISHED'}

class AOBJ_OT_MoveSequence(bpy.types.Operator):
    bl_idname = "aobj.move_sequence"
    bl_label = "Move Sequence"
    bl_options = {'REGISTER', 'UNDO'}
    
    direction: bpy.props.EnumProperty(items=[('UP', 'Up', ''), ('DOWN', 'Down', '')])
    
    def execute(self, context):
        obj = context.object
        settings = obj.aobj_anim_settings
        
        idx = settings.active_index
        if self.direction == 'UP' and idx > 0:
            settings.sequences.move(idx, idx - 1)
            settings.active_index -= 1
        elif self.direction == 'DOWN' and idx < len(settings.sequences) - 1:
            settings.sequences.move(idx, idx + 1)
            settings.active_index += 1
        
        return {'FINISHED'}

class ExportAnimatedOBJBinary(bpy.types.Operator, ExportHelper):
    """Export mesh with animation to Binary Animated OBJ format"""
    bl_idname = "export_scene.aobj_binary"
    bl_label = "Export Animated OBJ (Binary)"
    bl_options = {'PRESET'}

    filename_ext = ".aobj"
    filter_glob: StringProperty(default="*.aobj", options={'HIDDEN'})
    
    frame_step: IntProperty(
        name="Frame Step",
        description="Sample every Nth frame",
        default=1,
        min=1,
        max=10,
    )
    
    apply_modifiers: BoolProperty(
        name="Apply Modifiers",
        default=True,
    )
    
    global_scale: FloatProperty(
        name="Scale",
        default=1.0,
        min=0.001,
        max=1000.0,
    )

    def execute(self, context):
        obj = context.active_object
        
        if not obj or obj.type != 'MESH':
            self.report({'ERROR'}, "No active mesh object selected")
            return {'CANCELLED'}
        
        if not hasattr(obj, "aobj_anim_settings") or len(obj.aobj_anim_settings.sequences) == 0:
            self.report({'WARNING'}, "No animation sequences defined. Add them in Object Properties > AOBJ Animation Sequences")
        
        original_frame = context.scene.frame_current
        
        try:
            with open(self.filepath, 'wb') as f:
                context.scene.frame_set(0)
                base_mesh, base_obj_ref = self.get_mesh(context, obj)
                base_verts = [v.co.copy() for v in base_mesh.vertices]
                
                self.write_obj_geometry(f, obj, base_mesh)
                
                # Export sequences from object properties
                if hasattr(obj, "aobj_anim_settings"):
                    for anim_seq in obj.aobj_anim_settings.sequences:
                        self.write_animation_sequence(f, context, obj, base_verts, anim_seq)
                
                self.clear_mesh(base_mesh, base_obj_ref)
            
            self.report({'INFO'}, f"Exported {len(obj.aobj_anim_settings.sequences)} animations to {self.filepath}")
            return {'FINISHED'}
            
        except Exception as e:
            self.report({'ERROR'}, f"Export failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return {'CANCELLED'}
            
        finally:
            context.scene.frame_set(original_frame)

    def get_mesh(self, context, obj):
        depsgraph = context.evaluated_depsgraph_get()
        
        if self.apply_modifiers:
            obj_eval = obj.evaluated_get(depsgraph)
            mesh = obj_eval.to_mesh()
        else:
            mesh = obj.to_mesh()
        
        if self.global_scale != 1.0:
            for v in mesh.vertices:
                v.co *= self.global_scale
        
        return mesh, obj_eval if self.apply_modifiers else obj
    
    def clear_mesh(self, mesh, obj_reference):
        obj_reference.to_mesh_clear()

    def write_null_terminated_string(self, f, s):
        f.write(s.encode('utf-8'))
        f.write(struct.pack('B', 0))

    def write_obj_geometry(self, f, obj, mesh):
        vertex_data = bytearray()
        texcoord_data = bytearray()
        normal_data = bytearray()
        face_data = bytearray()
        
        f.write(struct.pack('B', KW_GROUP))
        self.write_null_terminated_string(f, obj.name)
        
        for v in mesh.vertices:
            vertex_data.extend(struct.pack('B', KW_VERTEX))
            vertex_data.extend(struct.pack('<fff', v.co.x, v.co.y, v.co.z))
        
        has_uvs = mesh.uv_layers.active is not None
        if has_uvs:
            uv_layer = mesh.uv_layers.active.data
            for poly in mesh.polygons:
                for loop_index in poly.loop_indices:
                    uv = uv_layer[loop_index].uv
                    texcoord_data.extend(struct.pack('B', KW_TEXCOORD))
                    texcoord_data.extend(struct.pack('<ff', uv.x, uv.y))
        
        mesh.calc_normals_split()
        for loop in mesh.loops:
            n = loop.normal
            normal_data.extend(struct.pack('B', KW_NORMAL))
            normal_data.extend(struct.pack('<fff', n.x, n.y, n.z))
        
        uv_index = 0
        normal_index = 0
        
        for poly in mesh.polygons:
            if len(poly.loop_indices) != 3:
                continue
            
            face_data.extend(struct.pack('B', KW_FACE))
            
            for loop_index in poly.loop_indices:
                loop = mesh.loops[loop_index]
                v_idx = loop.vertex_index + 1
                uv_idx = (uv_index + 1) if has_uvs else 0
                n_idx = normal_index + 1
                
                if has_uvs:
                    uv_index += 1
                normal_index += 1
                
                face_data.extend(struct.pack('<III', v_idx, uv_idx, n_idx))
        
        f.write(vertex_data)
        f.write(texcoord_data)
        f.write(normal_data)
        f.write(face_data)

    def write_animation_sequence(self, f, context, obj, base_verts, anim_seq):
        anim_data = bytearray()
        
        for frame in range(anim_seq.start_frame, anim_seq.end_frame + 1, self.frame_step):
            context.scene.frame_set(frame)
            
            current_mesh, current_obj_ref = self.get_mesh(context, obj)
            current_verts = [v.co.copy() for v in current_mesh.vertices]
            
            moved_verts = []
            for i, (base, current) in enumerate(zip(base_verts, current_verts)):
                delta = current - base
                if delta.length > 0.0001:
                    moved_verts.append((i, delta))
            
            if moved_verts:
                anim_data.extend(struct.pack('B', KW_FRAME))
                
                for vert_idx, delta in moved_verts:
                    anim_data.extend(struct.pack('B', KW_VDELTA))
                    anim_data.extend(struct.pack('<I', vert_idx + 1))
                    anim_data.extend(struct.pack('<fff', delta.x, delta.y, delta.z))
            
            self.clear_mesh(current_mesh, current_obj_ref)
        
        f.write(struct.pack('B', KW_ANIM))
        self.write_null_terminated_string(f, anim_seq.name)
        f.write(struct.pack('B', anim_seq.fps))
        f.write(anim_data)

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "global_scale")
        layout.prop(self, "apply_modifiers")
        layout.prop(self, "frame_step")
        
        obj = context.active_object
        if obj and hasattr(obj, "aobj_anim_settings"):
            box = layout.box()
            box.label(text=f"Will export {len(obj.aobj_anim_settings.sequences)} animation(s)")
            for seq in obj.aobj_anim_settings.sequences:
                box.label(text=f"  • {seq.name} ({seq.start_frame}-{seq.end_frame})")

def menu_func_export(self, context):
    self.layout.operator(ExportAnimatedOBJBinary.bl_idname, text="Animated OBJ Binary (.aobj)")

def register():
    bpy.utils.register_class(AnimSequenceItem)
    bpy.utils.register_class(AnimSequenceSettings)
    bpy.utils.register_class(AOBJ_UL_AnimSequences)
    bpy.utils.register_class(AOBJ_OT_AddSequence)
    bpy.utils.register_class(AOBJ_OT_RemoveSequence)
    bpy.utils.register_class(AOBJ_OT_MoveSequence)
    bpy.utils.register_class(AOBJ_PT_AnimSequences)
    bpy.utils.register_class(ExportAnimatedOBJBinary)
    
    # Register properties on Object
    bpy.types.Object.aobj_anim_settings = PointerProperty(type=AnimSequenceSettings)
    
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)

def unregister():
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)
    
    del bpy.types.Object.aobj_anim_settings
    
    bpy.utils.unregister_class(ExportAnimatedOBJBinary)
    bpy.utils.unregister_class(AOBJ_PT_AnimSequences)
    bpy.utils.unregister_class(AOBJ_OT_MoveSequence)
    bpy.utils.unregister_class(AOBJ_OT_RemoveSequence)
    bpy.utils.unregister_class(AOBJ_OT_AddSequence)
    bpy.utils.unregister_class(AOBJ_UL_AnimSequences)
    bpy.utils.unregister_class(AnimSequenceSettings)
    bpy.utils.unregister_class(AnimSequenceItem)

if __name__ == "__main__":
    register()