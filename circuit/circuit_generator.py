import bpy
import math

def clear_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()

def create_smooth_circuit():
    # パラメータ
    road_width = 3.5  # 日本の道路幅
    num_segments = 256  # 高解像度
    
    # 道路、中央線、外側線の頂点・面データ
    road_vertices = []
    road_faces = []
    center_vertices = []
    center_faces = []
    edge_vertices = []
    edge_faces = []
    
    # 単一の数式で滑らかな閉ループを生成
    for i in range(num_segments):
        t = (i / num_segments) * 2 * math.pi
        
        # 滑らかなパラメトリック曲線（フーリエ級数による閉ループ）
        r = 25 + 6*math.cos(2*t) + 3*math.sin(3*t) + 1.5*math.cos(5*t)
        x = r * math.cos(t)
        y = r * math.sin(t)
        
        # 次の点で方向ベクトルを計算
        t_next = ((i+1) % num_segments / num_segments) * 2 * math.pi
        r_next = 25 + 6*math.cos(2*t_next) + 3*math.sin(3*t_next) + 1.5*math.cos(5*t_next)
        x_next = r_next * math.cos(t_next)
        y_next = r_next * math.sin(t_next)
        
        # 方向ベクトルを正規化
        dx = x_next - x
        dy = y_next - y
        length = math.sqrt(dx*dx + dy*dy)
        if length > 0:
            dx /= length
            dy /= length
        
        # 垂直ベクトル
        nx = -dy
        ny = dx
        
        # 道路面の頂点
        left_x = x + nx * road_width
        left_y = y + ny * road_width
        right_x = x - nx * road_width
        right_y = y - ny * road_width
        
        road_vertices.extend([
            (left_x, left_y, 0),
            (right_x, right_y, 0)
        ])
        
        # 中央線の頂点（幅10cm）
        center_width = 0.05
        center_vertices.extend([
            (x + nx * center_width, y + ny * center_width, 0.001),
            (x - nx * center_width, y - ny * center_width, 0.001)
        ])
        
        # 外側線の頂点（幅15cm、道路端から15cm内側）
        edge_width = 0.075
        edge_offset = road_width - 0.15
        edge_vertices.extend([
            (x + nx * (edge_offset + edge_width), y + ny * (edge_offset + edge_width), 0.001),
            (x + nx * (edge_offset - edge_width), y + ny * (edge_offset - edge_width), 0.001),
            (x - nx * (edge_offset - edge_width), y - ny * (edge_offset - edge_width), 0.001),
            (x - nx * (edge_offset + edge_width), y - ny * (edge_offset + edge_width), 0.001)
        ])
        
        # 面を生成
        next_i = (i + 1) % num_segments
        
        # 道路面
        v1 = i * 2
        v2 = i * 2 + 1
        v3 = next_i * 2 + 1
        v4 = next_i * 2
        road_faces.append((v1, v4, v3, v2))
        
        # 中央線面
        center_faces.append((v1, v4, v3, v2))
        
        # 外側線面（左右）
        ev1 = i * 4
        ev2 = i * 4 + 1
        ev3 = next_i * 4 + 1
        ev4 = next_i * 4
        edge_faces.append((ev1, ev4, ev3, ev2))  # 左側線
        
        ev5 = i * 4 + 2
        ev6 = i * 4 + 3
        ev7 = next_i * 4 + 3
        ev8 = next_i * 4 + 2
        edge_faces.append((ev5, ev8, ev7, ev6))  # 右側線
    
    # 道路面メッシュ作成
    road_mesh = bpy.data.meshes.new("Road")
    road_mesh.from_pydata(road_vertices, [], road_faces)
    road_mesh.update()
    road_obj = bpy.data.objects.new("Road", road_mesh)
    bpy.context.collection.objects.link(road_obj)
    
    # アスファルトマテリアル
    asphalt_mat = bpy.data.materials.new("Asphalt")
    asphalt_mat.use_nodes = True
    nodes = asphalt_mat.node_tree.nodes
    nodes.clear()
    principled = nodes.new('ShaderNodeBsdfPrincipled')
    principled.inputs[0].default_value = (0.15, 0.15, 0.15, 1.0)
    output = nodes.new('ShaderNodeOutputMaterial')
    asphalt_mat.node_tree.links.new(principled.outputs[0], output.inputs[0])
    road_obj.data.materials.append(asphalt_mat)
    
    # 中央線メッシュ作成
    center_mesh = bpy.data.meshes.new("CenterLine")
    center_mesh.from_pydata(center_vertices, [], center_faces)
    center_mesh.update()
    center_obj = bpy.data.objects.new("CenterLine", center_mesh)
    bpy.context.collection.objects.link(center_obj)
    
    # 外側線メッシュ作成
    edge_mesh = bpy.data.meshes.new("EdgeLines")
    edge_mesh.from_pydata(edge_vertices, [], edge_faces)
    edge_mesh.update()
    edge_obj = bpy.data.objects.new("EdgeLines", edge_mesh)
    bpy.context.collection.objects.link(edge_obj)
    
    # 白線マテリアル
    white_mat = bpy.data.materials.new("WhiteLines")
    white_mat.use_nodes = True
    nodes = white_mat.node_tree.nodes
    nodes.clear()
    principled = nodes.new('ShaderNodeBsdfPrincipled')
    principled.inputs[0].default_value = (1.0, 1.0, 1.0, 1.0)
    output = nodes.new('ShaderNodeOutputMaterial')
    white_mat.node_tree.links.new(principled.outputs[0], output.inputs[0])
    
    center_obj.data.materials.append(white_mat)
    edge_obj.data.materials.append(white_mat)
    
    # スムースシェーディング適用
    for obj in [road_obj, center_obj, edge_obj]:
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.faces_shade_smooth()
        bpy.ops.object.mode_set(mode='OBJECT')
        obj.select_set(False)

def setup_lighting():
    # ワールド設定
    if bpy.context.scene.world is None:
        world = bpy.data.worlds.new("World")
        bpy.context.scene.world = world
    
    bpy.context.scene.world.use_nodes = True
    nodes = bpy.context.scene.world.node_tree.nodes
    nodes.clear()
    
    background = nodes.new('ShaderNodeBackground')
    background.inputs[0].default_value = (0.5, 0.7, 1.0, 1.0)
    background.inputs[1].default_value = 1.0
    
    output = nodes.new('ShaderNodeOutputWorld')
    bpy.context.scene.world.node_tree.links.new(background.outputs[0], output.inputs[0])

def main():
    clear_scene()
    create_smooth_circuit()
    setup_lighting()
    print("滑らかな道路サーキットが作成されました!")

if __name__ == "__main__":
    main()