import math
import numpy as np

# Custom
import pygarment as pyg
from . import skirt_paneled as skirts

# 插入的版片
class Insert(pyg.Panel):
    def __init__(self, id, width=30, depth=30) -> None:
        super().__init__(f'Insert_{id}')

        self.edges = pyg.esf.from_verts([0, 0], [width/2, depth], [width, 0], loop=True)

        self.interfaces = [
            pyg.Interface(self, self.edges[:2])
        ]
        self.top_center_pivot()
        self.center_x()

# 鱼尾裙
class GodetSkirt(pyg.Component):
    def __init__(self, body, design) -> None:
        super().__init__(f'{self.__class__.__name__}')

        gdesign = design['godet-skirt']
        ins_w = gdesign['insert_w']['v']
        ins_depth = gdesign['insert_depth']['v']

        base_skirt = getattr(skirts, gdesign['base']['v'])
        self.base = base_skirt(body, design)

        # 如果base是Skirt2或SkirtWB，插入深度不能超过裙长
        if(gdesign['base']['v'] == "Skirt2"):
            ins_depth = min(ins_depth, design['skirt']['length']['v']-1)
        # 如果base是PencilSkirt，插入深度+省道深度不能超过裙长
        if(gdesign['base']['v'] == 'PencilSkirt'):
            dart_depth = body['hips_line']*(design['pencil-skirt']['front_dart']['v'] + design['pencil-skirt']['rise']['v']) / 2
            skirt_length = round(design['pencil-skirt']['length']['v'] * body['leg_length'], 2)
            ins_depth = min(ins_depth, skirt_length - dart_depth - 1)

        bintr = self.base.interfaces['bottom']
        for edge, panel in zip(bintr.edges, bintr.panel):
            self.inserts(
                edge, panel, ins_w, ins_depth , 
                num_inserts=gdesign['num_inserts']['v'] / len(bintr),  # 如果下裙有2片，6个inserts平均到2片上是每片3个
                cuts_dist=gdesign['cuts_distance']['v'])

        self.interfaces = {
            'top': self.base.interfaces['top']
        }


    def inserts(self, bottom_edge, panel, ins_w, ins_depth, num_inserts=3, cuts_dist=0):
        """ Create insert panels, 
            add cuts to the skirt panel, 
            and connect created insert panels with them
        """

        num_inserts = int(num_inserts)
        bottom_len = bottom_edge.length()

        pbbox = panel.bbox3D()
        z_transl = panel.translation[-1] + np.sign(panel.translation[-1]) * 5
        y_base = pbbox[0][1]   # min Y
        x_shift = (pbbox[0][0] + pbbox[1][0]) / 2

        # 根据指定的插入物片宽度、插入片深度生成一个插入片
        insert = Insert(0, width=ins_w, depth=ins_depth).translate_by([
            x_shift - num_inserts * ins_w / 2 + ins_w / 2, y_base + ins_depth, z_transl])
        # 根据指定的插入片个数生成若干个插入片
        self.subs += pyg.ops.distribute_horisontally(insert, num_inserts, -ins_w, panel.name)

        # 用勾股定理计算切口的等腰三角形腰长（和插入片的等腰三角形腰长一致）
        side_len = math.sqrt((ins_w / 2)**2 + ins_depth**2)

        # 根据切口间距和插入片的个数计算切口宽度
        cut_width = (bottom_len - cuts_dist * num_inserts) / num_inserts 
        if cut_width < 1:
            cut_width = 1  # 1 cm 
            cuts_dist_req = cuts_dist
            cuts_dist = (bottom_len - cut_width * num_inserts) / num_inserts
            print(f'{self.__class__.__name__}::WARNING:: Cannot place {num_inserts} cuts '
                  f'with requested distance between cuts ({cuts_dist_req}). '
                  f'Using the maximum possible distance ({cuts_dist})')

        # 根据切口宽度和切口腰长判断切口能否构成三角形，如果无法构成则重新调整切口宽度
        if side_len > cut_width / 2: # Normal case，能构成三角形
            cut_depth = math.sqrt(side_len**2 - (cut_width / 2)**2)
        else: # cut_width太宽，无法构成三角形
            old_cut_width = cut_width
            cut_depth = 1
            cut_width = 2 * math.sqrt(side_len**2 - cut_depth**2) # 重置cut_width使之能构成三角形
            print(f'{self.__class__.__name__}::WARNING::Requested cut_width ({old_cut_width:.2f}) '
                  'is too wide for given inserts. '
                  f'Using the maximum possible width ({cut_width:.2f})')
        
        cut_shape = pyg.esf.from_verts([0,0], [cut_width / 2, cut_depth], [cut_width, 0])  

        right = z_transl < 0    # NOTE: heuristic corresponding to skirts in our collection

        for i in range(num_inserts):
            offset = cut_width / 2 + (cuts_dist / 2 if i == 0 else cuts_dist)   #  start_offest + i * stride

            new_bottom, cutted, _ = pyg.ops.cut_into_edge(
                cut_shape, bottom_edge, offset=offset, right=right)
            panel.edges.substitute(bottom_edge, new_bottom)
            bottom_edge = new_bottom[-1]  # New edge that needs to be cutted -- on the next step

            cut_interface = pyg.Interface(panel, cutted)
            if right: 
                cut_interface.reverse()

            self.stitching_rules.append(
                (self.subs[-1-i if right else -(num_inserts-i)].interfaces[0], 
                cut_interface))
       
