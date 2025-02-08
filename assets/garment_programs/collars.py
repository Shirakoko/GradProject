import numpy as np
from scipy.spatial.transform import Rotation as R

# Custom
import pygarment as pyg

# Other assets

from .bands import BandPanel
from .circle_skirt import CircleArcPanel


# V领：直接连接领点和领肩点
def VNeckHalf(depth, width, **kwargs):
    """Simple VNeck design"""

    edges = pyg.EdgeSequence(pyg.Edge([0, 0], [width / 2,-depth]))
    
    return edges

# 方形领口
def SquareNeckHalf(depth, width, **kwargs):
    """Square design"""

    edges = pyg.esf.from_verts([0, 0], [0, -depth], [width / 2, -depth])
    
    return edges

# 梯形领口
def TrapezoidNeckHalf(depth, width, angle=90, **kwargs):
    """Trapesoid neck design"""

    # Special case when angle = 180 (sin = 0)
    if (pyg.utils.close_enough(angle, 180, tol=1) 
            or pyg.utils.close_enough(angle, 0, tol=1)):
        # degrades into VNeck
        return VNeckHalf(depth, width)

    angle = np.deg2rad(angle)

    edges = pyg.esf.from_verts([0, 0], [-depth * np.cos(angle) / np.sin(angle), -depth], [width / 2, -depth])

    return edges


# S形弧线领口
def CurvyNeckHalf(depth, width, flip=False, bezier_controlpoint_x1 = 0.2, bezier_controlpoint_y1 = 0.3, bezier_controlpoint_x2 = 0.4, bezier_controlpoint_y2 = 0.3, **kwargs):
    """Testing Curvy Collar design"""

    sign = -1 if flip else 1
    edges = pyg.EdgeSequence(pyg.CurveEdge(
        [0, 0], [width / 2,-depth], 
        [[bezier_controlpoint_x1, sign * bezier_controlpoint_y1], [bezier_controlpoint_x2, -sign * bezier_controlpoint_y2]])) # 两个贝塞尔曲线的控制点的相对坐标
    
    return edges

# 两段弧线领口
def CircleArcNeckHalf(depth, width, angle=90, flip=False, **kwargs):
    """Collar with a side represented by a circle arc"""
    
    # 1/4 of a circle
    edges = pyg.EdgeSequence(pyg.CircleEdge.from_points_angle(
        [0, 0], [width / 2,-depth], arc_angle=np.deg2rad(angle),
        right=(not flip)
    ))

    return edges

# 一段弧线领口
def CircleNeckHalf(depth, width, **kwargs):
    """Collar that forms a perfect circle arc when halfs are stitched"""

    # 用三个点确定一段弧线
    circle = pyg.CircleEdge.from_three_points([0, 0], [width, 0], [width / 2, -depth])
    # Take a full desired arc and half it!
    subdiv = circle.subdivide_len([0.5, 0.5])

    return pyg.EdgeSequence(subdiv[0])


# # ------ Collars with panels ------

class NoPanelsCollar(pyg.Component):
    """Face collar class that only only forms the projected shapes """
    
    def __init__(self, name, body, design) -> None:
        super().__init__(name)

        # Front
        collar_type = globals()[design['collar']['f_collar']['v']]
        f_collar = collar_type(
            design['collar']['fc_depth']['v'],
            design['collar']['width']['v'], 
            angle=design['collar']['fc_angle']['v'], 
            flip=design['curvy_collar']['f_flip_curve']['v'],
            bezier_controlpoint_x1 = design['curvy_collar']['f_bezier_controlpoint_x1']['v'],
            bezier_controlpoint_y1 = design['curvy_collar']['f_bezier_controlpoint_y1']['v'],
            bezier_controlpoint_x2 = design['curvy_collar']['f_bezier_controlpoint_x2']['v'],
            bezier_controlpoint_y2 = design['curvy_collar']['f_bezier_controlpoint_y2']['v'])

        # Back
        collar_type = globals()[design['collar']['b_collar']['v']]
        b_collar = collar_type(
            design['collar']['bc_depth']['v'], 
            design['collar']['width']['v'], 
            angle=design['collar']['bc_angle']['v'],
            flip=design['curvy_collar']['b_flip_curve']['v'],
            bezier_controlpoint_x1 = design['curvy_collar']['b_bezier_controlpoint_x1']['v'],
            bezier_controlpoint_y1 = design['curvy_collar']['b_bezier_controlpoint_y1']['v'],
            bezier_controlpoint_x2 = design['curvy_collar']['b_bezier_controlpoint_x2']['v'],
            bezier_controlpoint_y2 = design['curvy_collar']['b_bezier_controlpoint_y2']['v'])
        
        self.interfaces = {
            'front_proj': pyg.Interface(self, f_collar),
            'back_proj': pyg.Interface(self, b_collar)
        }

# 方形领
class Turtle(pyg.Component):

    def __init__(self, tag, body, design) -> None:
        super().__init__(f'Turtle_{tag}')

        depth = design['collar']['component']['depth']['v']

        # --Projecting shapes--
        
        # 方形领强制用CircleNeckHalf领口
        width = design['collar']['width']['v']
        fc_height = design['collar']['fc_depth']['v']
        bc_height = design['collar']['bc_depth']['v']
        # 如果深度（弧高）＞0.5*宽度（弦长），说明是优弧，要把深度钳制在半径内
        if fc_height > 0.5*width:
            design['collar']['fc_depth']['v'] = 0.5*width
        if bc_height > 0.5*width:
            design['collar']['bc_depth']['v'] = 0.5*width
        
        f_collar = CircleNeckHalf(
            design['collar']['fc_depth']['v'],
            design['collar']['width']['v'])
        b_collar = CircleNeckHalf(
            design['collar']['bc_depth']['v'],
            design['collar']['width']['v'])

        design['collar']['f_collar']['v'] = design['collar']['b_collar']['v'] = "CircleNeckHalf"
        
        self.interfaces = {
            'front_proj': pyg.Interface(self, f_collar),
            'back_proj': pyg.Interface(self, b_collar)
        }

        # -- Panels --
        length_f, length_b = f_collar.length(), b_collar.length()
        height_p = body['height'] - body['head_l'] + depth

        # 前后领片都用BandPanel
        self.front = BandPanel(
            f'{tag}_turtle_front', length_f, depth).translate_by([-length_f / 2, height_p, 10])
        self.back = BandPanel(
            f'{tag}_turtle_back', length_b, depth).translate_by([-length_b / 2, height_p, -10])

        self.stitching_rules.append((
            self.front.interfaces['right'], 
            self.back.interfaces['right']
        ))

        self.interfaces.update({
            'front': self.front.interfaces['left'],
            'back': self.back.interfaces['left'],
            'bottom': pyg.Interface.from_multiple(
                self.front.interfaces['bottom'],
                self.back.interfaces['bottom']
            )
        })

# 一片扇形领
class SimpleLapelPanel(pyg.Panel):
    """A panel for the front part of simple Lapel"""
    def __init__(self, name, length, max_depth) -> None:
        super().__init__(name)

        self.edges = pyg.esf.from_verts(
            [0, 0], [max_depth, 0], [max_depth, -length]
        )

        self.edges.append(
            pyg.CurveEdge(
                self.edges[-1].end, 
                self.edges[0].start, 
                [[0.7, 0.2]]
            )
        )

        self.interfaces = {
            'to_collar': pyg.Interface(self, self.edges[0]),
            'to_bodice': pyg.Interface(self, self.edges[1])
        }


class SimpleLapel(pyg.Component):

    def __init__(self, tag, body, design) -> None:
        super().__init__(f'Turtle_{tag}')

        depth = design['collar']['component']['depth']['v']
        standing = design['collar']['component']['lapel_standing']['v']

        # --Projecting shapes--
        # 扇形领的前领口可以是任意形状的领口
        collar_type = globals()[design['collar']['f_collar']['v']]
        f_collar = collar_type(
            design['collar']['fc_depth']['v'],
            design['collar']['width']['v'], 
            angle=design['collar']['fc_angle']['v'], 
            flip=design['curvy_collar']['f_flip_curve']['v'],
            bezier_controlpoint_x1 = design['curvy_collar']['f_bezier_controlpoint_x1']['v'],
            bezier_controlpoint_y1 = design['curvy_collar']['f_bezier_controlpoint_y1']['v'],
            bezier_controlpoint_x2 = design['curvy_collar']['f_bezier_controlpoint_x2']['v'],
            bezier_controlpoint_y2 = design['curvy_collar']['f_bezier_controlpoint_y2']['v'])
        
        # 扇形领的后领口强制用CircleNeckHalf领口
        b_collar = CircleNeckHalf(
            design['collar']['bc_depth']['v'],
            design['collar']['width']['v'])
        
        self.interfaces = {
            'front_proj': pyg.Interface(self, f_collar),
            'back_proj': pyg.Interface(self, b_collar)
        }

        # -- Panels --
        length_f, length_b = f_collar.length(), b_collar.length()
        height_p = body['height'] - body['head_l'] + depth * 2
        
        self.front = SimpleLapelPanel(
            f'{tag}_lapel_front', length_f, depth).translate_by([-depth * 2, height_p, 30])

        if standing:
            self.back = BandPanel(
                f'{tag}_lapel_back', length_b, depth).translate_by([-length_b / 2, height_p, -10])
        else:
            # A curved back panel that follows the collar opening
            rad, angle, _ = b_collar[0].as_radius_angle()
            self.back = CircleArcPanel(
                f'{tag}_lapel_back', rad, depth, angle  
            ).translate_by([-length_b, height_p, -10])
            self.back.rotate_by(R.from_euler('XYZ', [90, 45, 0], degrees=True))


        self.stitching_rules.append((
            self.front.interfaces['to_collar'], 
            self.back.interfaces['right'] if standing else self.back.interfaces['left']
        ))

        self.interfaces.update({
            #'front': NOTE: no front interface here
            'back': self.back.interfaces['left'] if standing else self.back.interfaces['right'],
            'bottom': pyg.Interface.from_multiple(
                self.front.interfaces['to_bodice'],
                self.back.interfaces['bottom'] if standing else self.back.interfaces['top'],
            )
        })


