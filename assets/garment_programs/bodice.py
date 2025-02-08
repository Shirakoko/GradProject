from copy import copy, deepcopy
import numpy as np

# Custom
import pygarment as pyg

# other assets
from . import sleeves
from . import collars
from . import tee

# 前片（一半）
class BodiceFrontHalf(pyg.Panel):
    def __init__(self, name, body, design, side_dart_depth = 1, bottom_dart_depth = 1) -> None:
        super().__init__(name)
        

        m_bust = body['bust'] # 上胸围
        m_waist = body['waist'] # 腰围

        # sizes   
        max_len = body['waist_over_bust_line'] # 从胸线到腰线的侧边线长度
        bust_point = body['bust_points'] / 2 # 胸点到中轴线的距离

        # 前片分数：[(上胸围 - 背宽度)/2] / 上胸围
        front_frac = (body['bust'] - body['back_width']) / 2 / m_bust

        self.width = front_frac * m_bust    # (上胸围 - 背宽度)/2，前片横向最宽的宽度
        waist = front_frac * m_waist        # (上胸围 - 背宽度)/2 * (腰围/胸围)，前片横向最宽的宽度*腰围和胸围的比值。腰部宽度
        shoulder_incl = (sh_tan:=np.tan(np.deg2rad(body['shoulder_incl']))) * self.width # sh_tan为肩膀和水平线的倾角
        bottom_d_width = (self.width - waist) * 2 / 3

        # side length is adjusted due to shoulder inclination
        # for the correct sleeve fitting
        fb_diff = (2*front_frac - 0.5) * m_bust # (上胸围 - 背宽度) - 0.5*上胸围 = 0.5 * 上胸围 - 背宽度，也即前片和后片宽度差
        side_len = body['waist_line'] - sh_tan * fb_diff # 领口到腰部的垂线长 - sh_tan * 前片和后片宽度差 = 领口到腰部的垂线长 - 前片和后片长度差

        # 无袖前片由5个点围成，底边有一个额外的点用于得到省道的正确连接关系
        self.edges = pyg.esf.from_verts(
            [0, 0],                               # 肚脐位置的点（前片底边中点）作为原点
            [-m_waist / 4 - bottom_d_width, 0],   # 额外的点用于得到省道的正确连接关系
            [-self.width, 0],                     # 底边顶点之一，靠近身侧的点
            [-self.width, max_len],               # 胳肢窝下面的点
            [0, max_len + shoulder_incl],         # 领窝点
            loop=True
        )

        front_bottom_part_edge = self.edges[1]

        # 侧边省道
        bust_line = body['waist_line'] - body['bust_line']
        side_d_depth = side_dart_depth * (self.width - bust_point) # 省道深度：省道深度参数 * (前片横向最宽的宽度 - 胸点到中轴线的距离)，省道参数在0到1之间表明省道深度不得超过胸点
        side_d_width = max_len - side_len # 省道宽度：从胸线到腰线的侧边线长度 - 实际需要的侧边线长度
        s_edge, s_dart_edges, side_interface = pyg.ops.cut_into_edge(
            pyg.esf.dart_shape(side_d_width, side_d_depth), 
            self.edges[2], 
            offset=bust_line + side_d_width / 2, right=True)
        self.edges.substitute(2, s_edge)
        self.stitching_rules.append(
            (pyg.Interface(self, s_dart_edges[0]), pyg.Interface(self, s_dart_edges[1])))

        # 底边省道
        b_edge, b_dart_edges, b_interface = pyg.ops.cut_into_edge(
            # pyg.esf.dart_shape(bottom_d_width, 1. * bust_line),                 # 源码的做法是直接用1.0作为底边省道深度参数乘以胸腰垂直距离作为底边省道深度最终值
            pyg.esf.dart_shape(bottom_d_width, bottom_dart_depth * bust_line),    # 这里引入底边省道深度参数
            self.edges[0], 
            offset=bust_point, right=True)
        self.edges.substitute(0, b_edge)
        self.stitching_rules.append(
            (pyg.Interface(self, b_dart_edges[0]), pyg.Interface(self, b_dart_edges[1])))

        # Take some fabric from side in the bottom 
        front_bottom_part_edge.end[0] = - (waist + bottom_d_width)

        # Interfaces
        self.interfaces = {
            'outside':  pyg.Interface(self, side_interface),   # side_interface,    # pyg.Interface(self, [side_interface]),  #, self.edges[-3]]),
            'inside': pyg.Interface(self, self.edges[-1]),
            'shoulder': pyg.Interface(self, self.edges[-2]),
            'bottom_front': pyg.Interface(self, b_interface),
            'bottom_back': pyg.Interface(self, front_bottom_part_edge),
            
            # Reference to the corner for sleeve and collar projections
            'shoulder_corner': pyg.Interface(self, [self.edges[-3], self.edges[-2]]),
            'collar_corner': pyg.Interface(self, [self.edges[-2], self.edges[-1]])
        }

        # default placement
        self.translate_by([0, body['height'] - body['head_l'] - max_len, 0])

# 后片（一半）
class BodiceBackHalf(pyg.Panel):
    """Panel for the front/back of upper garments"""

    def __init__(self, name, body, design, bottom_dart_depth=1) -> None:
        super().__init__(name)

        # account for ease in basic measurements
        m_bust = body['bust']
        m_waist = body['waist']

        # Overall measurements
        length = body['waist_line']
        back_fraction = body['back_width'] / body['bust'] / 2
        
        self.width = back_fraction * m_bust
        waist = back_fraction * m_waist
        waist_width = self.width - (self.width - waist) / 3   # slight inclination on the side

        shoulder_incl = np.tan(np.deg2rad(body['shoulder_incl'])) * self.width

        # Base edge loop
        self.edges = pyg.esf.from_verts(
            [0, 0], 
            [-waist_width, 0],
            [-self.width, body['waist_line'] - body['bust_line']],  # from the bottom
            [-self.width, length],   
            [0, length + shoulder_incl],   # Add some fabric for the neck (inclination of shoulders)
            loop=True)
        
        self.interfaces = {
            'outside': pyg.Interface(self, [self.edges[1], self.edges[2]]),  #, self.edges[3]]),
            'inside': pyg.Interface(self, self.edges[-1]),
            'shoulder': pyg.Interface(self, self.edges[-2]),
            # Reference to the corners for sleeve and collar projections
            'shoulder_corner': pyg.Interface(self, pyg.EdgeSequence(self.edges[-3], self.edges[-2])),
            'collar_corner': pyg.Interface(self, pyg.EdgeSequence(self.edges[-2], self.edges[-1]))
        }

        # Bottom dart as cutout -- for straight line
        bottom_d_width = (self.width - waist) * 2 / 3
        bottom_d_depth = bottom_dart_depth * (length - body['bust_line'])  # calculated value
        bottom_d_position = body['bust_points'] / 2

        b_edge, b_dart_edges, b_interface = pyg.ops.cut_into_edge(
            pyg.esf.dart_shape(bottom_d_width, bottom_d_depth), self.edges[0], 
            offset=bottom_d_position, right=True)

        self.edges.substitute(0, b_edge)
        self.interfaces['bottom'] = pyg.Interface(self, b_interface)

        # default placement
        self.translate_by([0, body['height'] - body['head_l'] - length, 0])

        # Stitch the dart
        self.stitching_rules.append((pyg.Interface(self, b_dart_edges[0]), pyg.Interface(self, b_dart_edges[1])))

# 前片的一半+后片的一半，包含袖子和领子
class BodiceHalf(pyg.Component):
    """Definition of a half of an upper garment with sleeves and collars"""

    def __init__(self, name, body, design, fitted=True, fs_dart_depth=1, fb_dart_depth=1, bb_dart_depth=1) -> None:
        super().__init__(name)

        design = deepcopy(design)   # Recalculate freely!

        # Torso
        if fitted: # 如果是紧身上衣，用Bodice类
            self.ftorso = BodiceFrontHalf(f'{name}_ftorso', body, design, side_dart_depth=fs_dart_depth, bottom_dart_depth=fb_dart_depth).translate_by([0, 0, 25]) # 用fs_dart_depth传递前片侧边省道深度参数
            self.btorso = BodiceBackHalf(f'{name}_btorso', body, design, bottom_dart_depth=bb_dart_depth).translate_by([0, 0, -20]) # 用bb_dart_depth传递后片底边省道深度参数
        else: # 如果不是紧身上衣，用tee类（宽松T恤）
            self.ftorso = tee.TorsoFrontHalfPanel(f'{name}_ftorso', body, design).translate_by([0, 0, 25])
            self.btorso = tee.TorsoBackHalfPanel(f'{name}_btorso', body, design).translate_by([0, 0, -20])

        # Interfaces
        self.interfaces.update({
            'f_bottom': self.ftorso.interfaces['bottom_front'],
            'b_bottom': pyg.Interface.from_multiple(
                self.btorso.interfaces['bottom'], self.ftorso.interfaces['bottom_back']),
            'front_in': self.ftorso.interfaces['inside'],
            'back_in': self.btorso.interfaces['inside']
        })

        # 袖子和领口裁切
        self.eval_dep_params(body, design)
        if design['shirt']['strapless']['v']: # 无袖无领
            self.make_strapless(design)
        else:
            # 添加袖子和领子
            self.add_sleeves(name, body, design)
            self.add_collars(name, body, design)
            self.stitching_rules.append((
                self.ftorso.interfaces['shoulder'], 
                self.btorso.interfaces['shoulder']
            ))  # tops

        # Main connectivity
        self.stitching_rules.append((self.ftorso.interfaces['outside'], self.btorso.interfaces['outside']))   # sides


    def eval_dep_params(self, body, design):

        # Sleeves
        # NOTE assuming the vertical side is the first argument
        max_cwidth = self.ftorso.interfaces['shoulder_corner'].edges[0].length() - 1  # 达到最长的袖笼弧线-1
        min_cwidth = body['armscye_depth'] # 肩周宽度
        v = design['sleeve']['connecting_width']['v'] # v表示0到1之间的插值参数
        design['sleeve']['connecting_width']['v'] = min_cwidth + v * (max_cwidth - min_cwidth) # 在min_cwidth和max_cwidth之间插值

        # Collars
        # NOTE: Assuming the first is the top edge
        # Width
        max_edge = self.ftorso.interfaces['collar_corner'].edges[0]
        # NOTE: Back panel is more narrow, so using it
        max_w = 2 * (self.btorso.width - design['sleeve']['inclination']['v'] - 1) # 最大值是（后片宽度-袖子插入-1）*2
        min_w = body['neck_w'] # 最小值是脖子宽度

        if design['collar']['width']['v'] >= 0: # 如果width是[0,1]的正数，width在min_w到max_w之间插值
            design['collar']['width']['v'] = width = pyg.utils.lin_interpolation(min_w, max_w, design['collar']['width']['v'])
        else: # 如果是[-0.5，0]的负数，width在0到min_w之间插值
            design['collar']['width']['v'] = width = pyg.utils.lin_interpolation(0, min_w, 1 + design['collar']['width']['v'])

        # Depth
        # Collar depth is given w.r.t. length.
        # adjust for the shoulder inclination
        tg = np.tan(np.deg2rad(body['shoulder_incl']))      # tg为肩膀角度的正切值
        f_depth_adj = tg * (self.ftorso.width - width / 2)  # 前片领口深度调整，领口最浅的深度
        b_depth_adj = tg * (self.btorso.width - width / 2)  # 后片领口深度调整，领口最浅的深度

        max_f_len = self.ftorso.interfaces['collar_corner'].edges[1].length() - tg * self.ftorso.width - 1  # 前领口最深的深度
        max_b_len = self.btorso.interfaces['collar_corner'].edges[1].length() - tg * self.btorso.width - 1  # 后领口最深的深度

        # 计算前领深度
        design['collar']['f_strapless_depth'] = {}                                                                  # 新开一个字段，表示无袖时的领点
        design['collar']['f_strapless_depth']['v'] = design['collar']['fc_depth']['v'] * max_f_len                  # [0,1] * max_f_len
        fc_height = design['collar']['fc_depth']['v'] = design['collar']['f_strapless_depth']['v'] + f_depth_adj    # 重新设置深度
        # 如果深度（弧高）＞0.5*宽度（弦长），说明是优弧，要把深度钳制在半径内
        if design['collar']['f_collar']['v']=="CircleNeckHalf" and fc_height > 0.5*width:
            design['collar']['fc_depth']['v'] = 0.5*width
        
        # 计算后领深度
        design['collar']['b_strapless_depth'] = {}
        design['collar']['b_strapless_depth']['v'] = design['collar']['bc_depth']['v'] * max_b_len
        bc_height = design['collar']['bc_depth']['v'] = design['collar']['b_strapless_depth']['v'] + b_depth_adj
        if design['collar']['b_collar']['v']=="CircleNeckHalf" and bc_height > 0.5*width:
            design['collar']['bc_depth']['v'] = 0.5*width


    def add_sleeves(self, name, body, design):

        diff = self.ftorso.width - self.btorso.width

        self.sleeve = sleeves.Sleeve(name, body, design, depth_diff=diff)

        _, f_sleeve_int = pyg.ops.cut_corner(
            self.sleeve.interfaces['in_front_shape'].projecting_edges(), 
            self.ftorso.interfaces['shoulder_corner'])
        _, b_sleeve_int = pyg.ops.cut_corner(
            self.sleeve.interfaces['in_back_shape'].projecting_edges(), 
            self.btorso.interfaces['shoulder_corner'])

        if not design['sleeve']['sleeveless']['v']:  
            # Ordering
            bodice_sleeve_int = pyg.Interface.from_multiple(
                f_sleeve_int.reverse(),
                b_sleeve_int.reverse())
            self.stitching_rules.append((
                self.sleeve.interfaces['in'], 
                bodice_sleeve_int
            ))
            self.sleeve.place_by_interface(
                self.sleeve.interfaces['in'], 
                bodice_sleeve_int, 
                gap=7
            )
    
    def add_collars(self, name, body, design):
        # Front
        collar_type = getattr(
            collars, 
            str(design['collar']['component']['style']['v']), 
            collars.NoPanelsCollar
            )
        
        self.collar_comp = collar_type(name, body, design)
        
        # Project shape
        _, fc_interface = pyg.ops.cut_corner(
            self.collar_comp.interfaces['front_proj'].edges, 
            self.ftorso.interfaces['collar_corner']
        )
        _, bc_interface = pyg.ops.cut_corner(
            self.collar_comp.interfaces['back_proj'].edges, 
            self.btorso.interfaces['collar_corner']
        )

        # Add stitches/interfaces
        if 'bottom' in self.collar_comp.interfaces:
            self.stitching_rules.append((
                pyg.Interface.from_multiple(fc_interface, bc_interface), 
                self.collar_comp.interfaces['bottom']
            ))

        # Upd front interfaces accordingly
        if 'front' in self.collar_comp.interfaces:
            self.interfaces['front_collar'] = self.collar_comp.interfaces['front']
            self.interfaces['front_in'] = pyg.Interface.from_multiple(
                self.ftorso.interfaces['inside'], self.interfaces['front_collar']
            )
        if 'back' in self.collar_comp.interfaces:
            self.interfaces['back_collar'] = self.collar_comp.interfaces['back']
            self.interfaces['back_in'] = pyg.Interface.from_multiple(
                self.btorso.interfaces['inside'], self.interfaces['back_collar']
            )

    def make_strapless(self, design):

        out_depth = design['sleeve']['connecting_width']['v']
        f_in_depth = design['collar']['f_strapless_depth']['v']
        b_in_depth = design['collar']['b_strapless_depth']['v']
        self._adjust_top_level(self.ftorso, out_depth, f_in_depth)
        self._adjust_top_level(self.btorso, out_depth, b_in_depth)

    def _adjust_top_level(self, panel, out_level, in_level):
        """NOTE: Assumes the top of the panel is a single edge
            and adjustment can be made vertically
        """

        panel_top = panel.interfaces['shoulder'].edges[0]
        min_y = min(panel_top.start[1], panel_top.end[1])  

        # Order vertices
        ins, out = panel_top.start, panel_top.end
        if panel_top.start[1] < panel_top.end[1]:
            ins, out = out, ins
  
        ins[1] = min_y - in_level
        out[1] = min_y - out_level

# 一件完整的衬衫
class Shirt(pyg.Component):
    """Panel for the front of upper garments with darts to properly fit it to the shape"""

    def __init__(self, body, design, fitted=False) -> None:
        name_with_params = f"{self.__class__.__name__}"
        super().__init__(name_with_params)

        if design['left']['enable_asym']['v']:
            if design['shirt']['strapless']['v'] != design['left']['shirt']['strapless']['v']:
                # Force no collars
                design = deepcopy(design)
                design['collar']['component']['style']['v'] = None
                design['left']['collar']['component']['style']['v'] = None

        self.right = BodiceHalf(f'right', body, design, fitted=fitted, 
            fs_dart_depth = design['torso_dart']['front_side_dart_depth']['v'],
            fb_dart_depth = design['torso_dart']['front_bottom_dart_depth']['v'],
            bb_dart_depth = design['torso_dart']['back_bottom_dart_depth']['v'])
        self.left = BodiceHalf(
            f'left', body, 
            design['left'] if design['left']['enable_asym']['v'] else design, 
            fitted=fitted, 
            fs_dart_depth = design['torso_dart']['front_side_dart_depth']['v'],
            fb_dart_depth = design['torso_dart']['front_bottom_dart_depth']['v'],
            bb_dart_depth = design['torso_dart']['back_bottom_dart_depth']['v']).mirror()

        self.stitching_rules.append((self.right.interfaces['front_in'], self.left.interfaces['front_in']))
        self.stitching_rules.append((self.right.interfaces['back_in'], self.left.interfaces['back_in']))

        # Adjust interface ordering for correct connectivity
        self.left.interfaces['b_bottom'].reverse()
        if fitted: 
            self.right.interfaces['f_bottom'].reorder([0, 1], [1, 0])

        self.interfaces = {   # Bottom connection
            'bottom': pyg.Interface.from_multiple(
                self.right.interfaces['f_bottom'],
                self.left.interfaces['f_bottom'],
                self.left.interfaces['b_bottom'],
                self.right.interfaces['b_bottom'],)
        }

# FittedShirt是Shirt的派生类
class FittedShirt(Shirt):
    """Creates fitted shirt
    
        NOTE: Separate class is used for selection convenience.
        Even though most of the processing is the same 
        (hence implemented with the same components except for panels), 
        design parametrization differs significantly. 
        With that, we decided to separate the top level names
    """
    def __init__(self, body, design) -> None:
        super().__init__(body, design, fitted=True)
