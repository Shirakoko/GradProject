import os
import sys
import json
import argparse
import re

from glob import glob
import numpy as np

# Makes core library available without extra installation steps
sys.path.insert(0, './external/')
sys.path.insert(1, './')
from external.pattern.rotation import euler_xyz_to_R

def sample_circle(start, end, circ_params, num_samples=10):
    from pygarment import CircleEdge
    radius, large_arc, right = circ_params
    edge = CircleEdge.from_points_radius(start, end, radius, large_arc, right)

    subedges = edge._subdivide([1.0/num_samples]*num_samples)
    verts = subedges.verts()
    verts = np.asarray(verts[::2] + verts[-1:])
    # rel coordinate to abs coordinate
    return verts


def sample_bezier(start, end, control_point, degree=2, num_samples=10):
    from geomdl import BSpline, utilities

    curve = BSpline.Curve()
    curve.degree = degree

    if degree == 2:
        curve.ctrlpts = [start.tolist(), control_point.tolist(), end.tolist()]
    else:
        curve.ctrlpts = [start.tolist(), control_point[0].tolist(), control_point[1].tolist(), end.tolist()]
    
    curve.knotvector = utilities.generate_knot_vector(curve.degree, len(curve.ctrlpts))
    # curve.delta = 0.01
    curve.sample_size = num_samples
    evalpts = np.array(curve.evalpts)

    return evalpts


def verts_to_style3d_coords(vertices, translation_2d):
    """Convert given vertices and panel (2D) translation to px coordinate frame & units"""
    # Put upper left corner of the bounding box at zero
    offset = np.min(vertices, axis=0)
    vertices = vertices - offset
    translation_2d = translation_2d + offset
    return vertices, translation_2d


def control_to_abs_coord(start, end, control_scale):
    """
    Derives absolute coordinates of Bezier control point given as an offset
    """
    edge = end - start
    edge_perp = np.array([-edge[1], edge[0]])

    control_start = start + control_scale[0] * edge
    control_point = control_start + control_scale[1] * edge_perp

    return control_point 


# return true if the curve is clockwise, else false
def check_winding_order(edge_seq, verts):
    ordered_verts = []
    for idx in range(1, len(edge_seq)):
        assert edge_seq[idx]["endpoints"][0] == edge_seq[idx-1]["endpoints"][1], "Edge sequence is not continuous!"

    verts = np.array(verts)
    ordered_verts = np.array([x['endpoints'][0] for x in edge_seq] + [0], dtype=int)
    ordered_verts = verts[ordered_verts]

    wind_checker =  np.sum(
        (ordered_verts[1:, 0] - ordered_verts[:-1, 0]) * \
        (ordered_verts[1:, 1] + ordered_verts[:-1, 1])
        )

    return wind_checker > 0


def convert_edge_seq(edge_seq, verts, to_spline=False):
    for idx in range(1, len(edge_seq)):
        assert edge_seq[idx]["endpoints"][0] == edge_seq[idx-1]["endpoints"][1], "Edge sequence is not continuous!"

    verts = np.array(verts)
    verts = verts - np.mean(verts, axis=0, keepdims=True)

    new_edge_seq = []

    for idx, edge in enumerate(edge_seq):
        start, end = verts[edge['endpoints'][0]], verts[edge['endpoints'][1]]
        
        if 'curvature' in edge:
            if isinstance(edge['curvature'], list) or edge['curvature']['type'] == 'quadratic':  
                control_scale = edge['curvature'] if isinstance(edge['curvature'], list) else \
                            edge['curvature']['params'][0]
                control_point = control_to_abs_coord(start, end, control_scale)

                if True:
                    evalpts = sample_bezier(start, end, control_point, degree=2, num_samples=5)
                    new_evalpts = np.zeros((evalpts.shape[0], 3))
                    new_evalpts[:, :2] = evalpts
                    new_edge_seq.append({
                        "id": str(idx),
                        "bezierPoints": [[0, 0, 0], [0, 0, 0]],
                        "controlPoints": new_evalpts.tolist()
                    })    

                else:
                    new_edge_seq.append({
                        "id": str(idx),
                        "bezierPoints": [(control_point[0]-start).tolist() + [0.], [0., 0., 0.]],
                        "controlPoints": [start.tolist() + [0.], end.tolist() + [0.]]
                    })


            elif edge['curvature']['type'] == 'circle':
                evalpts = sample_circle(start, end, edge['curvature']['params'], num_samples=5)

                new_evalpts = np.zeros((evalpts.shape[0], 3))
                new_evalpts[:, :2] = evalpts
                new_edge_seq.append({
                    "id": str(idx),
                    "bezierPoints": [[0, 0, 0], [0, 0, 0]],
                    "controlPoints": new_evalpts.tolist()
                })
                
                
            elif edge['curvature']['type'] == 'cubic':
                control_point = np.array([control_to_abs_coord(start, end, p) for p in edge['curvature']['params']])

                if to_spline:
                    evalpts = sample_bezier(start, end, control_point, degree=3, num_samples=5)
                    new_evalpts = np.zeros((evalpts.shape[0], 3))
                    new_evalpts[:, :2] = evalpts
                    new_edge_seq.append({
                        "id": str(idx),
                        "bezierPoints": [[0, 0, 0], [0, 0, 0]],
                        "controlPoints": new_evalpts.tolist()
                    })
                    
                else:
                    new_edge_seq.append({
                        "id": str(idx),
                        "bezierPoints": [(control_point[0]-start).tolist() + [0.], (control_point[1]-end).tolist() + [0.]],
                        "controlPoints": [start.tolist() + [0.], end.tolist() + [0.]]
                    })

        else:
            new_edge_seq.append({
                "id": str(idx),
                "bezierPoints": [[0, 0, 0], [0, 0, 0]],
                "controlPoints": [start.tolist() + [0.], end.tolist() + [0.]]
            })
    
    return new_edge_seq
    
# 将传入的panel_name进行匹配，返回对应的label
def panel_name_to_label(panel_name):
    label = None
    # 需要匹配的字符串列表
    # find_list = ["turtle","lapel","shoulder","sleeve","sl_","ftorso","btorso","wb","front","pant_f","back","pant_b","cuff_skirt"]
    # 匹配字典
    match_dict = {"turtle":"neck","lapel":"neck","shoulder":"shoulder","sleeve":"arm","sl_":"wrist","ftorso":"bodyfront","btorso":"bodyback",
                  "wb":"waist","front":"pelvisfront","pant_f":"pelvisfront","back":"pelvisback","pant_b":"pelvisback","skirt_f":"pelvisfront","skirt_b":"pelvisback","cuff_skirt":"foot"}

    # 遍历find_list中需要匹配的字符串片段
    for name_seg, match_label in match_dict.items():
        match = re.search(name_seg, panel_name) # 判断传入的panel_name中是否含有上述字符串片段
        if(match): # 如果包含
            label = match_label # 赋值label
            break
        else: # 如果不包含，就继续检测下一个
            continue

    return label

def get_panel_center(panel, is_ccw: bool = False,max_panel_width=50):

    panel_center = np.asarray(panel['translation'][:2])
    verts_center = np.mean(np.asarray(panel['vertices']), axis=0)
    panel_center = panel_center + verts_center

    if is_ccw:
        panel_center[0] = -panel_center[0]

    if panel['translation'][2] >= 0: panel_center[0] = panel_center[0] + max_panel_width
    else: panel_center[0] = panel_center[0] - max_panel_width

    return panel_center.tolist()

def get_panel_center_3d(panel, translation):
    panel_center = np.asarray(translation)
    panel_rotation = np.asarray(panel["rotation"])
    rotation_matrix = euler_xyz_to_R(panel_rotation)
    verts_center = np.mean(np.asarray(panel['vertices']), axis=0)
    rotated_verts_center = np.array(rotation_matrix.dot(verts_center)).squeeze()
    panel_center = panel_center + rotated_verts_center
    return panel_center.tolist()

def flip_panel(panel):
    panel["vertices"] = [[-vert[0], vert[1], 0] for vert in panel["vertices"]]
    for i in range(len(panel["edges"])):
        panel["edges"][i]["bezierPoints"] = [[-point[0], point[1]] for point in panel["edges"][i]["bezierPoints"]]
        panel["edges"][i]["controlPoints"] = [[-point[0], point[1]] for point in panel["edges"][i]["controlPoints"]]
    return panel

def scale_panel(panel, scale: float):
    panel["vertices"] = [[scale*vert[0], scale*vert[1]] for vert in panel["vertices"]]
    for i in range(len(panel["edges"])):
        panel["edges"][i]["bezierPoints"] = [[scale*point[0], scale*point[1]] for point in panel["edges"][i]["bezierPoints"]]
        panel["edges"][i]["controlPoints"] = [[scale*point[0], scale*point[1]] for point in panel["edges"][i]["controlPoints"]]
    panel["center"] = (np.array(panel["center"], dtype=float) * scale).tolist()
    panel["translation"] = (np.array(panel["translation"], dtype=float) * scale).tolist()
    return panel

def convert_segment_to_stitch_segment(segment, is_first: bool, is_neck: bool):
    cloth_id = segment["panel"]
    edge_id = str(segment["edge"])
    if is_neck:
        is_first = not is_first
    if is_first:
        return {
            "start": {
                "clothPieceId": cloth_id,
                "edgeId": edge_id,
                "param": 0
            },
            "end": {
                "clothPieceId": cloth_id,
                "edgeId": edge_id,
                "param": 1
            },
            "isCounterClockWise": False
        }
    else:
        return {
            "start": {
                "clothPieceId": cloth_id,
                "edgeId": edge_id,
                "param": 1
            },
            "end": {
                "clothPieceId": cloth_id,
                "edgeId": edge_id,
                "param": 0
            },
            "isCounterClockWise": True
        }

# 把garmentcode的json格式转换成我们需要的panels.json的格式，传入的是字典字符串，以及输出路径
def convert_form_from_str(dic_str, out_fp):
    try:
        json_str = dic_str
        # 获取原始的板片和缝纫线数据
        panels = json_str["pattern"]["panels"]
        stitches = json_str["pattern"]["stitches"]
        # 创建一个空的字典，用于存储目标的板片和缝纫线数据
        result = {}

        # 创建一个空的列表，用于存储目标的板片数据
        result["panels"] = []
        # 用于缝纫线特殊判断翻领
        panel_label_map = {}
        # 遍历原始的板片数据
        for key, panel_data in panels.items():
            # 创建一个空的字典，用于存储目标板片数据
            panel = {}
            # 设置板片的id，先用板片名称即key代替
            panel["id"] = key
            # 设置板片的label，调用panel_name_to_label()得到label
            panel["label"] = panel_name_to_label(key)
            panel_label_map[key] = True if re.search("lapel", key) else False

            # 设置板片的顶点，先用原始的顶点数据代替
            panel["vertices"] = [vert+[.0] for vert in panel_data["vertices"]]

            # 判断原始版片的方向
            is_ccw = check_winding_order(panel_data["edges"], panel["vertices"])
            
            # 转换板片的边
            panel["edges"] = convert_edge_seq(panel_data["edges"], panel_data["vertices"], to_spline=False)

            # 转换板片的bbox中心
            panel["center"] = get_panel_center(panel_data, is_ccw)
            # print(f'{key} panel center: {panel["center"]}')

            # 3D旋转(角度制)
            panel["rotation"] = panel_data["rotation"]

            # 翻转
            if not (is_ccw ^ (not panel_label_map[key])):
                panel = flip_panel(panel)
                panel["rotation"] = [
                    panel_data["rotation"][0],
                    panel_data["rotation"][1] + 180,
                    panel_data["rotation"][2]
                ]

            # 3D位置
            panel["translation"] = get_panel_center_3d(panel, panel_data["translation"])

            # 单位标准化
            panel = scale_panel(panel, 1000/json_str["properties"]["units_in_meter"])

            # 将板片数据添加到列表中
            result["panels"].append(panel)

        # 创建一个空的列表，用于存储目标的缝纫线数据
        result["stitches"] = []
        # 遍历原始的缝纫线数据
        for stitch in stitches:
            # 创建一个空的列表，用于存储目标的缝纫线数据
            stitch_result = []
            # 第一段缝纫线
            key0 = stitch[0]["panel"]
            stitch_result.append(convert_segment_to_stitch_segment(stitch[0], True, panel_label_map[key0]))
            # 第二段缝纫线
            key1 = stitch[1]["panel"]
            stitch_result.append(convert_segment_to_stitch_segment(stitch[1], False, panel_label_map[key1]))
            # 将缝纫线数据添加到列表中
            result["stitches"].append(stitch_result)

        # 最后将对象转换成json字符串，缩进为4
        result_json = json.dumps(result, indent=4)
        with open(out_fp, 'w', encoding='utf-8') as f:
            # 用json.dump()函数把json字符串写入文件
            f.write(result_json)
            f.close()

        # print('[DONE] processing %s' % out_fp) # 后面也会打印处理完毕，这里就不用了
        return True
    except Exception as e:
        print('[FAILED] processing %s: %s' % (out_fp, e))
        return False


# if __name__ == '__main__':
#     parser = argparse.ArgumentParser(description="Convert GarmentCode spec to pattern.json")
#     parser.add_argument("-i", "--input", type=str, help="Input spec path.")
#     parser.add_argument("-o", "--output", default='output.json', type=str, help="Output file path.")
    
#     args, cfg_cmd = parser.parse_known_args()

#     if os.path.isdir(args.input):
#         input_files = glob(os.path.join(args.input, '**', '*.json'), recursive=True)
#         succee_cnt = 0
#         for input_file in input_files:
#             succee_cnt += int(convert_form(
#                 input_file, 
#                 os.path.join(
#                     os.path.dirname(input_file), 
#                     os.path.basename(args.output)
#                 )))
            
#         print('[DONE] processing %d files, %d succeed, %d failed' % (len(input_files), succee_cnt, len(input_files)-succee_cnt))

#     else:
#         convert_form(args.input, args.output)
