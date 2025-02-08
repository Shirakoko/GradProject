# 这个脚本用来生成所有可能的的yaml组合，跑起来可能比较慢
import os
import sys
from pathlib import Path
import yaml
import itertools
import argparse
from datetime import datetime
from copy import deepcopy
from enum import Enum

# Makes core library available without extra installation steps
sys.path.insert(0, './external/')
sys.path.insert(1, './')

# Custom
from assets.garment_programs.skirt_paneled import *
from assets.garment_programs.tee import *
from assets.garment_programs.godet import *
from assets.garment_programs.bodice import *
from assets.garment_programs.pants import *
from assets.garment_programs.meta_garment import *
from assets.garment_programs.bands import *

from assets.body_measurments.body_params import BodyParameters

_BODY_MEASUREMENTS = {
    'avg': 'assets/body_measurments/f_smpl_avg.yaml',
    'thin': 'assets/body_measurments/f_smpl_thin.yaml',
    'full-bodied': 'assets/body_measurments/f_smpl_full_bodied.yaml',
    'man': 'assets/body_measurments/m_smpl_avg.yaml'
}

class Upper(Enum):
    SHIRT = "Shirt"
    FITTEDSHIRT = "FittedShirt"

class Bottom(Enum):
    SKIRTCIRCLE = "SkirtCircle" # 圆形裙
    GODETSKIRT = "GodetSkirt" # 鱼尾裙
    # PANTS = "Pants"
    SKIRT2 = "Skirt2" # 下摆没有弧度的梯形裙
    # SKIRTMANYPANELS = "SkirtManyPanels"
    PENCILSKIRT = "PencilSkirt" # 包臀裙
    # SKIRTLEVELS = "SkirtLevels" # 两层拼接裙，目前来说比较复杂，暂时不要

class Wb(Enum):
    TRUE = True
    FALSE = False


# 定义一个函数，用于遍历字典，找出所有的range字段
def find_range(dic, ranges):
    # 遍历字典的键值对
    for key, value in dic.items(): 
        # 如果值是一个字典，就递归地继续遍历
        if isinstance(value, dict):
            if("range" in value): # 如果发现range字段是这个字典的key
                ranges.append({key:value['range']}) # 把它的上级键名称和它的取值列表以键值对的形式加入列表ranges中
                continue # 直接进行下一轮循环
            else: # 如果range不是其中的键，继续寻找
                find_range(value, ranges)

    return

# 定义一个函数，找出所有键名为name的含有range的键值对并放入ranges列表中
def find_range(dic,ranges,name):
    if(name in dic and isinstance(dic[name], dict)):
        if("range" in dic[name]):
            ranges.append({name:dic[name]['range']})
    else:
        for value in dic.values():
            if isinstance(value,dict):
                find_range(value,ranges,name)
    return


# 定义一个函数，用于删除某个键值对/子字典，直接对原字典进行操作
def del_sub_dic(dic, key):
    if key in dic:
        del dic[key]
    for value in dic.values():
        if isinstance(value, dict):
            del_sub_dic(value, key)
    return dic

# # 定义一个函数，用于根据range字段可能选取的值，生成所有的其他组合
# def generate_combinations(dic, result, keys, origin_dic, max_piece = 10):
#     file_idx = 0
#     # 遍历每个组合
#     for combination in itertools
# 这个脚本用来生成所有可能的的yaml组合，跑起来可能比较慢
import os
import sys
from pathlib import Path
import yaml
import itertools
import argparse
from datetime import datetime
from copy import deepcopy
from enum import Enum

# Makes core library available without extra installation steps
sys.path.insert(0, './external/')
sys.path.insert(1, './')

# Custom
from assets.garment_programs.skirt_paneled import *
from assets.garment_programs.tee import *
from assets.garment_programs.godet import *
from assets.garment_programs.bodice import *
from assets.garment_programs.pants import *
from assets.garment_programs.meta_garment import *
from assets.garment_programs.bands import *

from assets.body_measurments.body_params import BodyParameters

_BODY_MEASUREMENTS = {
    'avg': 'assets/body_measurments/f_smpl_avg.yaml',
    'thin': 'assets/body_measurments/f_smpl_thin.yaml',
    'full-bodied': 'assets/body_measurments/f_smpl_full_bodied.yaml',
    'man': 'assets/body_measurments/m_smpl_avg.yaml'
}

class Upper(Enum):
    SHIRT = "Shirt"
    FITTEDSHIRT = "FittedShirt"

class Bottom(Enum):
    SKIRTCIRCLE = "SkirtCircle" # 圆形裙
    GODETSKIRT = "GodetSkirt" # 鱼尾裙
    # PANTS = "Pants"
    SKIRT2 = "Skirt2" # 下摆没有弧度的梯形裙
    # SKIRTMANYPANELS = "SkirtManyPanels"
    PENCILSKIRT = "PencilSkirt" # 包臀裙
    # SKIRTLEVELS = "SkirtLevels" # 两层拼接裙，目前来说有点复杂，暂时不要

class Wb(Enum):
    TRUE = True
    FALSE = False


# 定义一个函数，用于遍历字典，找出所有的range字段
def find_range(dic, ranges):
    # 遍历字典的键值对
    for key, value in dic.items():
        # 如果值是一个字典，就递归地继续遍历
        if isinstance(value, dict):
            if("range" in value): # 如果发现range字段是这个字典的key
                ranges.append({key:value['range']}) # 把它的上级键名称和它的取值列表以键值对的形式加入列表ranges中
                continue # 直接进行下一轮循环
            else: # 如果range不是其中的键，继续寻找
                find_range(value, ranges)

    return

# 定义一个函数，找出所有键名为name的含有range的键值对并放入ranges列表中
def find_range(dic,ranges,name):
    if(name in dic and isinstance(dic[name], dict)):
        if("range" in dic[name]):
            ranges.append({name:dic[name]['range']})
    else:
        for value in dic.values():
            if isinstance(value,dict):
                find_range(value,ranges,name)
    return


# 定义一个函数，用于删除某个键值对/子字典，直接对原字典进行操作
def del_sub_dic(dic, key):
    if key in dic:
        del dic[key]
    for value in dic.values():
        if isinstance(value, dict):
            del_sub_dic(value, key)
    return dic

# # 定义一个函数，从传入的ranges键值对列表中drop掉一些不需要变化的range
# def drop_range(ranges, name):
#     if(type(ranges) is list):
#         for range in ranges:
#             if (name in range):
#                 ranges.remove(range)
#                 break
#     else:
#         print("ranges不是一个列表")
#     return

# 从给出的键中找到子字典的引用
def find_sub_dic(str,origin_dic):
    sub_dic = None
    # 遍历字典的键值对
    for key, value in origin_dic.items(): 
        if(key==str):
            sub_dic = origin_dic[key]
            break
        elif isinstance(value, dict):
            result = find_sub_dic(str, value)
            if result is not None:
                sub_dic = result
                break
    return sub_dic

# 从原字典中找到子字典，并修改它的value字段
def alter_range_value(key,origin_dic,range_value):
    if(key in origin_dic and isinstance(origin_dic[key], dict)):
        if("v" in origin_dic[key]):
            origin_dic[key]["v"] = range_value
    else:
        for value in origin_dic.values():
            if isinstance(value,dict):
                alter_range_value(key, value, range_value)
    return

# 定义一个函数，把字典的键和值转换成字符串再放入列表，来处理键值对列表ranges
def ranges_to_keys_and_result(ranges):
    keys = [list(dic.keys())[0] for dic in ranges]
    result = [list(dic.values())[0] for dic in ranges]
    return keys, result

# 定义一个函数，用于根据range字段可能选取的值，生成所有的其他组合
def generate_combinations(dic, result, keys, origin_dic, max_piece = 10):
    # 用itertools.product生成所有可能的组合
    combinations = itertools.product(*result)

    file_idx = 0
    # 遍历每个组合
    for combination in combinations:
        if(file_idx>=max_piece): # 检查当前文件编号是不是超过最多想要生成的个数
            break

        new_dic = deepcopy(dic)
        file_idx += 1
        # 依次将combination中的每个元素更新到字典中
        for i in range(0,len(combination)):
            sub_dic = find_sub_dic(keys[i], new_dic)
            if(type(sub_dic) is dict and sub_dic is not None):
                sub_dic["v"] = combination[i]
            else:
                print("sub_dic为空")

        expand_dic_to_origin(new_dic,origin_dic) # 扩充字典
        remove_prefix(new_dic) # 去除键名前缀
    
        design_data = new_dic['design']
        try:
            piece = MetaGarment(str(file_idx), body, design_data)
            pattern = piece()

            folder = pattern.serialize( # 序列化成json字符串
                path = args.output,
                # tag=datetime.now().strftime("%y%m%d-%H-%M-%S"),
                tag = '',
                to_subfolder=True, 
                with_3d=False, with_text=False, view_ids=False)
            
            print(f'[DONE] {piece.name} saved to {folder}')

        except Exception as e:
            print(f'[FAILED] {str(file_idx)} : {e}')

        # 生成所有其他组合并保存为新的YAML文件
        # with open(folderpath+'/'+str(file_idx)+'.yaml', 'w') as file:
        #     yaml.dump(new_dic, file)
        # print('\n')
    return

# 将收缩的字典扩充回原来的origin_dic，防止生成patterns.json时报错
def expand_dic_to_origin(new_dic,origin_dic):        
    for key, value in origin_dic['design'].items(): # 遍历origin_dic中的键值对
        if key not in new_dic['design']: # 如果在new_dic中没有，就添加
            new_dic['design'][key] = value
    return

# 将字典中所有u_\w_\c_\s_\b_开头的去掉前缀
def remove_prefix(dic):
    for key in list(dic['design']['waistband']):
        if key.startswith("w_"):
            dic['design']['waistband'][key[2:]] = dic['design']['waistband'].pop(key)
        
    for key in list(dic['design']['collar']):
        if key.startswith("c_"):
            dic['design']['collar'][key[2:]] = dic['design']['collar'].pop(key)
    
    dic['design']['collar']['component']['style'] = dic['design']['collar']['component'].pop('c_style')
    
    for key in list(dic['design']['sleeve']):
        if key.startswith("s_"):
            dic['design']['sleeve'][key[2:]] = dic['design']['sleeve'].pop(key)
    
    for key in list(dic['design']['shirt']):
        if key.startswith("u_"):
            dic['design']['shirt'][key[2:]] = dic['design']['shirt'].pop(key)

    for key in list(dic['design']['skirt']):
        if key.startswith("b_"):
            dic['design']['skirt'][key[2:]] = dic['design']['skirt'].pop(key)

    for key in list(dic['design']['flare-skirt']):
        if key.startswith("b_"):
            dic['design']['flare-skirt'][key[2:]] = dic['design']['flare-skirt'].pop(key)

    for key in list(dic['design']['godet-skirt']):
        if key.startswith("b_"):
            dic['design']['godet-skirt'][key[2:]] = dic['design']['godet-skirt'].pop(key)

    for key in list(dic['design']['levels-skirt']):
        if key.startswith("b_"):
            dic['design']['levels-skirt'][key[2:]] = dic['design']['levels-skirt'].pop(key)

    for key in list(dic['design']['pencil-skirt']):
        if key.startswith("b_"):
            dic['design']['pencil-skirt'][key[2:]] = dic['design']['pencil-skirt'].pop(key)

    for key in list(dic['design']['pants']):
        if key.startswith("b_"):
            dic['design']['pants'][key[2:]] = dic['design']['pants'].pop(key)
    
    if "b_type" in dic['design']['pants']['cuff']:
        dic['design']['pants']['cuff']['type'] = dic['design']['pants']['cuff'].pop('b_type')

    return

# 指定上衣（含袖子是不是None）
def assign_upper(origin_dic,dic,upper_option: Upper, has_sleeve = True):
    upper_option = upper_option.value
    del_sub_dic(dic,"upper") # 因为已经指定了，就从可变项中删除
    del_sub_dic(dic,"meta")
    if upper_option == None: # 没有上衣的话上衣、领子、袖子都是不可变的了
        alter_range_value("upper",origin_dic,None)
        del_sub_dic(dic,"shirt"), del_sub_dic(dic,"collar"), del_sub_dic(dic,"sleeve")
    elif upper_option == "Shirt" or upper_option == "FittedShirt":
        if upper_option == "Shirt":
            alter_range_value("upper",origin_dic,"Shirt")
        else:
            alter_range_value("upper",origin_dic,"FittedShirt")
        del_sub_dic(dic,"s_sleeveless")
        if has_sleeve == False:
            alter_range_value("s_sleeveless",origin_dic,True)
            del_sub_dic(dic,"sleeve")
        else:
            alter_range_value("s_sleeveless",origin_dic,False)
    return

# 指定腰带
def assign_wb(origin_dic,dic,has_wb: Wb):
    has_wb = has_wb.value
    del_sub_dic(dic,"wb")
    if has_wb is False:
        alter_range_value("wb",origin_dic,False)
        del_sub_dic(dic,"waistband")
    else:
        alter_range_value("wb",origin_dic,True)
    return
        
# 指定下半身
def assign_bottom(origin_dic,dic,bottom_option: Bottom):
    bottom_option = bottom_option.value
    del_sub_dic(dic,"bottom")
    key_list = ["skirt","flare-skirt","godet-skirt","pencil-skirt","levels-skirt","pants"]
    if bottom_option == None:
        alter_range_value("bottom",origin_dic,None)
        for key in key_list:
            del_sub_dic(dic,key)
    elif bottom_option == "SkirtCircle":
        alter_range_value("bottom",origin_dic,"SkirtCircle")
        for key in key_list:
            if key != "flare-skirt":
                del_sub_dic(dic,key)
    elif bottom_option == "GodetSkirt":
        alter_range_value("bottom",origin_dic,"GodetSkirt")
        for key in key_list:
            if key != "godet-skirt":
                del_sub_dic(dic,key)
    elif bottom_option == "Pants":
        alter_range_value("bottom",origin_dic,"Pants")
        for key in key_list:
            if key != "pants":
                del_sub_dic(dic,key)
    elif bottom_option == "Skirt2":
        alter_range_value("bottom",origin_dic,"Skirt2")
        for key in key_list:
            if key != "skirt":
                del_sub_dic(dic,key)
    elif bottom_option == "PencilSkirt":
        alter_range_value("bottom",origin_dic,"PencilSkirt")
        for key in key_list:
            if key != "pencil-skirt":
                del_sub_dic(dic,key)
    elif bottom_option == "SkirtLevels":
        alter_range_value("bottom",origin_dic,"SkirtLevels")
        for key in key_list:
            if key != "levels-skirt":
                del_sub_dic(dic,key)
    return


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Convert GarmentCode spec to pattern.json")
    parser.add_argument("-b", "--body", type=str, choices=['avg', 'thin', 'full-bodied', 'man'], default='thin', help="Body to use.") # 人体尺寸文件
    parser.add_argument("-o", "--output", type=str, default='./Logs', help="Output file path.") # 输出路径
    parser.add_argument("-p", "--piece", type=int, default=10, help='how many pieces you want to generate, to limit the number of pieces') # 生成多少件之后停止生成

    args, cfg_cmd = parser.parse_known_args()

    body = BodyParameters(_BODY_MEASUREMENTS[args.body]) # 从四种人体尺寸配置文件中选取其中一种作为身体参数
    piece_num = args.piece

    # 打开模板tamplate.yaml文件
    with open("template.yaml") as f:
        # 使用 pyyaml 的 load() 函数，把文件内容转换成字典
        origin_dic = yaml.load(f, Loader=yaml.FullLoader)
        # 因为原字典是不能动的，要复制一份
        shrink_dic = deepcopy(origin_dic)
        # 先去除允许不对称的可变字段leftyi
        del_sub_dic(shrink_dic,"left")
        # 指定上衣 Shirt
        assign_upper(origin_dic,shrink_dic,upper_option=Upper.FITTEDSHIRT,has_sleeve=False)
        # 指定腰带 False
        assign_wb(origin_dic,shrink_dic,has_wb=Wb.FALSE)
        # 指定下半身 PencilSkirt
        assign_bottom(origin_dic, shrink_dic,bottom_option=Bottom.GODETSKIRT)
        
        # 指定所有的可变字段列表
        changeable_fields = ["u_length","b_length","b_flare","u_width","b_base"]

        # 创建一个空列表，用于存储range字段和它的上级键
        ranges = []

        for field in changeable_fields:
            find_range(shrink_dic, ranges, field)

        keys, result = ranges_to_keys_and_result(ranges)
        print("配置文件中一共有",len(keys),"种可变字段")

        # 调用 generate_combinations() 函数生成所有的其他组合，注意，这里要传入origin_dic
        generate_combinations(shrink_dic, result, keys, origin_dic, max_piece=piece_num)