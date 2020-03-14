import win32com.client
import re
import keyboard
import os
import cv2
import time
import random
import numpy as np
import json
from PIL import ImageGrab
import threading
import codecs 
'test11'

keyboard.add_hotkey('end',os._exit,(0,))

player_list = {'台男':'白虎','明女':'阎王'}

dm = win32com.client.Dispatch('dm.dmsoft')

monster_info = {'阎王':[32589,1108100],'白虎':[12613,289255600],'结冰的士兵':[46148,150]}


def cv_imread(file_path,flags = -1):
    cv_img = cv2.imdecode(np.fromfile(file_path,dtype=np.uint8),flags)
    return cv_img

hungry_resource = cv_imread('G:/VS-source/repos/单角色挂机/单角色挂机/resource/hungry.bmp')
no_fight_resource = cv_imread('G:/VS-source/repos/单角色挂机/单角色挂机/resource/no_fight.bmp')
fighting_resource = cv_imread('G:/VS-source/repos/单角色挂机/单角色挂机/resource/fighting.bmp')
mask = cv_imread('G:/VS-source/repos/单角色挂机/单角色挂机/resource/mask.bmp',0)

def time_test(f):
    def wrapper(*args, **kwargs):
        time1 = time.time()
        res = f(*args, **kwargs)
        print('执行时间为:',time.time()-time1)
        return res
    return wrapper

    #模仿人点击左键，time为点击的次数，默认为1
def LeftClick(run_time = 1):
    for i in range(run_time):
        res1 = dm.LeftDown()
        time.sleep(random.uniform(0.035,0.085))
        res2 = dm.LeftUp()
        if i < run_time - 1:
            time.sleep(random.uniform(0.05,0.1))
    return res1 and res2

    #模仿人点击右键，time为点击的次数，默认为1
def RightClick(run_time = 1):
    for i in range(run_time):
        res = dm.RightDown()
        time.sleep(random.uniform(0.035,0.085))
        res = dm.RightUp() and res
        if i < run_time - 1:
            time.sleep(random.uniform(0.05,0.1))
    return res

    #模仿人点击某键，key为需要按的键，以字符串形式输入，time为点击的次数，默认为1
def KeyPress(key,run_time = 1):
    for i in range(run_time):
        res = dm.KeyDownChar(key)
        time.sleep(random.uniform(0.045,0.085))
        res = dm.KeyUpChar(key) and res
        if i < run_time - 1:
            time.sleep(random.uniform(0.05,0.1))
    return res

    #模拟键盘输入字符串
def OutputString(str):
    tmp_res = True
    for key in str:
        if KeyPress(key) is False:
            return False
        time.sleep(random.uniform(0.05,0.1))
    return True

    #模拟人工鼠标移动
def MoveTo(x,y):
    _,first_x,first_y = dm.GetCursorPos(0,0)
    now_x,now_y = first_x,first_y
    per_ms_speed = 5
    dist_x =  x - now_x
    dist_y =  y - now_y
    dist = (dist_x**2+dist_y**2)**0.5
    time_cost = int(dist/per_ms_speed)
    if dist_x == 0:
        per_x = 0
        if dist_y == 0:
            per_y = 0
        else:
            per_y = per_ms_speed*(dist_y/abs(dist_y))
    else:
        t = dist_y/dist_x
        per_x = per_ms_speed/(t**2+1)**0.5
        per_y = per_x*t
    zero_time = time.time()
    time_step = 0
    while time_step < time_cost:
        now_time = time.time()
        if now_time - zero_time > time_step*0.001:
            time_step = int((now_time - zero_time + 0.001)/0.001)
            now_x = round(first_x + per_x*time_step)
            now_y = round(first_y + per_y*time_step)
            dm.MoveTo(now_x,now_y)
    dm.MoveTo(x,y)
    return True

    #获取指定句柄的窗口在屏幕上的位置
def GetWindowRect(hwnd):
    tmp = [0]*4
    tmp = dm.GetWindowRect(hwnd,*tmp)
    return tmp

    #基于窗口位置移动鼠标
def MoveToInWindows(hwnd,x,y):
    if hwnd:
        res,x1,y1,x2,y2 = GetWindowRect(hwnd)        
        if x>0 and y>0 and x<x2-x1 and y<y2-y1:
            if res:
                return MoveTo(x1+x,y1+y)
    print('指定的点不合法')
    return False
    

    #把窗口坐标转换为屏幕坐标
def ClientToScreen(hwnd,x,y):
    loc = [0]*4
    _,*loc = dm.GetWindowRect(hwnd,*loc)
    return loc[0]+x,loc[1]+y

    #计算IoU
def calculate_IoU(candidateBound, groundTruthBound):
    cx1 = candidateBound[0]
    cy1 = candidateBound[1]
    cx2 = cx1+candidateBound[2]
    cy2 = cy1+candidateBound[3]

    gx1 = groundTruthBound[0]
    gy1 = groundTruthBound[1]
    gx2 = gx1+groundTruthBound[2]
    gy2 = gy1+groundTruthBound[3]

    carea = (cx2 - cx1) * (cy2 - cy1)
    garea = (gx2 - gx1) * (gy2 - gy1)

    x1 = max(cx1, gx1)
    y1 = max(cy1, gy1)
    x2 = min(cx2, gx2)
    y2 = min(cy2, gy2)
    w = max(0, x2 - x1)
    h = max(0, y2 - y1)
    area = w * h

    iou = area / (carea + garea - area)

    return iou

    #模板匹配
def Template_matching(img,template,threshold = 0.9):
    res = cv2.matchTemplate(img,template,cv2.TM_CCOEFF_NORMED)
    loc = np.array(np.where( res >= threshold))
    loc = list(zip(*loc[::-1]))
    if len(loc)>1:
        for num1,tmp_res1 in enumerate(loc):
            for num2,tmp_res2 in enumerate(loc):
                if num1 == num2:
                    continue
                IoU = calculate_IoU((tmp_res1[0],tmp_res1[1],template.shape[0],template.shape[1]),
                                    (tmp_res2[0],tmp_res2[1],template.shape[0],template.shape[1]))
                if IoU >0.5:
                    if res[tmp_res1[::-1]]>res[tmp_res2[::-1]]:
                        del loc[num2]
                    else:
                        del loc[num1]
    return loc

def Template_matching_in_box(template,bbox = None,threshold = 0.9):
    img = ImageGrab.grab(bbox)
    img = cv2.cvtColor(np.asarray(img),cv2.COLOR_RGB2BGR)
    return Template_matching(template,img,threshold)

def Template_matching_in_window(template,hwnd,bbox = None,threshold = 0.9):
    if bbox is None:
        _,bbox = GetWindowRect(hwnd)
    else:
        _,tmp = GetWindowRect(hwnd)
        bbox = (bbox[0]+tmp[0],bbox[1]+tmp[1],bbox[3]+tmp[0],bbox[4]+tmp[1])
    return Template_matching_in_box(template,bbox,threshold)

    #截图
#@time_test
def screen_shot_in_mem_front(hwnd):
    if hwnd:
        _,*tmp = GetWindowRect(hwnd)
        img = ImageGrab.grab(tmp)
        img = cv2.cvtColor(np.asarray(img),cv2.COLOR_RGB2BGR)
        return img
    return False

def EnumWindowByProcess(process_name,title,class_name,filter):
    hwnds = dm.EnumWindowByProcess(process_name,title,class_name,filter)
    return re.split(',',hwnds)

def find_mem_loc(hd,monster_id = 12613,power_num_min = 289255600):
    self_loc = result = dm.FindInt(hd,'00000000-FFFFFFFF',monster_id,monster_id,0)
    result = re.split('[|]',result )
    tmp = []
    min_address = 0xFF
    max_address = 0x00
    for i in result:
        zdl = dm.ReadInt(hd,i+'+28',0)
        if zdl>0 and zdl %power_num_min == 0:
            if int(i[:2],16)> max_address:
                max_address = int(i[:2],16)
            if int(i[:2],16)< min_address:
                min_address = int(i[:2],16)
    return hex(min_address)+'000000-'+hex(max_address)+'FFFFFF'

def dist(list):
    tmp = []
    for i in list:
        tmp.append(((i[0]**2+i[1]**2)**0.5,i))
    tmp.sort()
    return tmp

def monster_location(hd,mem_loc,monster_id = 12613,power_num_min = 289255600):
    result = dm.FindInt(hd,mem_loc,monster_id,monster_id,0)
    result = re.split('[|]',result )
    tmp = []
    for i in result:
        zdl = dm.ReadInt(hd,i+'+28',0)
        if zdl>0 and zdl %power_num_min == 0:     
            if dm.ReadInt(hd,i+'-18',0) == 0:
                loc = (int((dm.ReadInt(hd,i+'+300',1)-int(0x01fc))),
                        int((dm.ReadInt(hd,i+'+302',1)-int(0x011f))))
                if abs(loc[0])<430 and abs(loc[1])<320:
                    tmp.append(loc)
    if len(tmp)>0:
        tmp = dist(tmp)
        return (515+tmp[0][1][0],362+tmp[0][1][1])
    return False

#检索图片中某种颜色的位置,RGB为某种颜色,由于opencv的图片颜色为BGR形式所以需要变换
def search_color(img,RGB):
    a = np.where(img[:,:,2] == RGB[0])
    a = set(zip(a[0],a[1]))
    b = np.where(img[:,:,1] == RGB[1])
    b = set(zip(b[0],b[1]))
    c = np.where(img[:,:,0] == RGB[2])
    c = set(zip(c[0],c[1]))
    return np.array(list(zip(*((a&b)&c))))

#枚举图片中非[0,0,0]颜色的位置
def enumerate_color(img):
    size = img.shape
    color_list = []
    for x in range(size[0]):
        for y in range(size[1]):
            if img[x,y,0] >12 or img[x,y,1] >12 or img[x,y,2] >12:
                if not ([img[x,y,2],img[x,y,1],img[x,y,0]] in color_list):
                    color_list.append([img[x,y,2],img[x,y,1],img[x,y,0]])
    return color_list
    #box的宽为66像素,长为44像素

def calculate_loction(x,y,x2,y2,ratio=0.35):
    #x,y为起始点，x2，y2为目标点
    if ratio<0:
        tmp_x = x
        tmp_y = y
        x = x2
        y = y2
        x2 = tmp_x
        y2 = tmp_y
    ratio = abs(ratio)
    dx = x2 - x
    dy = y2 - y
    if ratio<1:
        distence = (dx**2+dy**2)**0.5*ratio
    else:
        distence = (dx**2+dy**2)**0.5-ratio
    if dx == 0:
        return int(x+0),int(y+distence*((dy>0)*2-1))
    if dy == 0:
        return int(x+distence*((dx>0)*2-1)),int(y+0)   
    k1 = (dy)/(dx)       
    x1 = distence/(k1**2+1)**0.5*((dx>0)*2-1)
    y1 = x1*k1
    return int(x1+x),int(y1+y)

class Gersang_window():
    #global mouse_lock,keyboard_lock,manager_dict
    def __init__(self,hwnd_num,log):
        self.hwnd_num = hwnd_num
        self.log = log
        return

    #寻找怪物
    def find_monster(self,monster_id = 12613,power_num_min = 289255600):
        while self.check_fight() is False:
            monster_loc = monster_location(self.hwnd_num,manager_dict[self.hwnd_num]['mem_loc'],monster_id,power_num_min)
            if monster_loc:
                self.mouse_operate(*monster_loc,'right')
            time.sleep(0.1)
        return True
    
    #吃饱食度
    def take_food(self,food_carryer):
        if self.check_hungry():
            self.keyborad_operate(food_carryer)
            self.keyborad_operate('i')
            while self.check_hungry():
                self.mouse_operate(616,411,'right')
                time.sleep(1)
            self.keyborad_operate('i')
        return True
    
    #检查是否需要吃饱食度
    def check_hungry(self):
        img = screen_shot_in_mem_front(self.hwnd_num)[690:709,211:246]
        is_hungry = Template_matching(img,hungry_resource)
        return len(is_hungry) > 0

    #检查是否战斗状态

    def check_fight(self):
        while True:
            img = screen_shot_in_mem_front(self.hwnd_num)
            no_fight = img[734:795,3:45]
            fighting = img[705:766,974:1008]
            is_no_fight = Template_matching(no_fight,no_fight_resource)
            is_fighting = Template_matching(fighting,fighting_resource)
            res_map = int(''.join(re.split(' ',dm.ReadData(self.hwnd_num,'023EA63C',4))[::-1]),16)
            check_is_fight = len(is_fighting) > 0
            check_no_fight = len(is_no_fight) > 0
            if check_is_fight and not check_no_fight and res_map>0:                
                manager_dict[self.hwnd_num]['is_fight'] = True
                return True
            if check_no_fight and not check_is_fight and res_map==0:   
                manager_dict[self.hwnd_num]['is_fight'] = False
                return False
            
    def mouse_operate(self,x,y,mod = 'None',run_time = 1):
        if mod == 'None':
            res = MoveToInWindows(self.hwnd_num,x,y)
        if mod == 'left':
            res = MoveToInWindows(self.hwnd_num,x,y)
            res = LeftClick(run_time) and res    
        if mod == 'right':
            res = MoveToInWindows(self.hwnd_num,x,y)
            res = RightClick(run_time) and res
        if mod == 'ctrl_left':
            res = MoveToInWindows(self.hwnd_num,x,y)
            res = dm.KeyDownChar('ctrl') and res
            time.sleep(0.075)
            res = LeftClick(run_time) and res
            time.sleep(0.075)
            res = dm.KeyUpChar('ctrl') and res
        if mod == 'ctrl_right':
            res = MoveToInWindows(self.hwnd_num,x,y)
            res = dm.KeyDownChar('ctrl') and res
            time.sleep(0.075)
            res = RightClick(run_time) and res
            time.sleep(0.075)
            res = dm.KeyUpChar('ctrl') and res
        return res
    
    def keyborad_operate(self,button,mod = 'None',run_time = 1):
        if mod == 'None':
            res = KeyPress(button,run_time)
        if mod == 'ctrl':
            res = dm.KeyDownChar('ctrl')
            time.sleep(0.075)
            res = KeyPress(button,run_time) and res
            time.sleep(0.075)
            res = dm.KeyUpChar('ctrl') and res
        return res

    def loc_camera(self):
        x_grid = dm.ReadInt(self.hwnd_num,'00A098F8',0)
        y_grid = dm.ReadInt(self.hwnd_num,'00A098FC',0)
        return [x_grid,y_grid]

    def loc_mouse(self):
        x_grid = dm.ReadInt(self.hwnd_num,'01E91D18',0)
        y_grid = dm.ReadInt(self.hwnd_num,'01E52C54',0)
        return [x_grid,y_grid]

    def complex_operation(self,x,y,skill_button=None,mouse_mod = 'None',keyborad_mod = 'None',distance = 0):
        camera_grid = self.loc_camera()
        mouse_grid = self.loc_mouse()
        scope = 5
        self.mouse_operate(515,386)
        if distance!=0:
            x,y = calculate_loction(*self.own_loc,x,y,distance)

        while abs(x-camera_grid[0])>scope or abs(y-camera_grid[1])>scope:
            if abs(x-camera_grid[0])>scope and abs(y-camera_grid[1])>scope:
                if x<camera_grid[0] and y<camera_grid[1]:
                    self.keyborad_operate('up')
                if x>camera_grid[0] and y>camera_grid[1]:
                    self.keyborad_operate('down')
                if x>camera_grid[0] and y<camera_grid[1]:
                    self.keyborad_operate('right')
                if x<camera_grid[0] and y>camera_grid[1]: 
                    self.keyborad_operate('left')
            elif abs(x-camera_grid[0])>scope:
                if x>camera_grid[0]:
                    self.keyborad_operate('right')
                    self.keyborad_operate('down')
                elif x<camera_grid[0]:
                    self.keyborad_operate('left')
                    self.keyborad_operate('up')
            elif abs(y-camera_grid[1])>scope:
                if y>camera_grid[1]:
                    self.keyborad_operate('left')
                    self.keyborad_operate('down')
                elif y<camera_grid[1]:
                    self.keyborad_operate('right')
                    self.keyborad_operate('up')
            camera_grid = self.loc_camera()
        mouse_grid = self.loc_mouse()
        x_dis = x - mouse_grid[0]
        y_dis = y - mouse_grid[1]
        screen_x = x_dis*32-y_dis*32
        screen_y = x_dis*16+y_dis*16
        if not skill_button is None:
            self.keyborad_operate(skill_button,keyborad_mod)
        self.mouse_operate(515+screen_x,386+screen_y,mouse_mod)
        self.mouse_operate(515,386)
        return True

    def unit_loc_inf(self):
        self.unit_loc = []
        self.dist_sorted = []
        size = 40
        map_adress = ''.join(re.split(' ',dm.ReadData(self.hwnd_num,'023EA63C',4))[::-1])
        map_list = re.split(' ',dm.ReadData(self.hwnd_num,map_adress,3200))
        for elem in map_list[2049:2070:2]:
            if int(elem,16)>=16:
                map_list = map_list[:2048]
                size = 32
                break
        tmp = []
        for num,elem in enumerate(map_list):
            if num%2==1:
                continue
            tmp.append(map_list[num+1]+map_list[num])
        map_list = tmp
        for num,elem in enumerate(map_list):
            map_list[num] = int(elem,16)
        unit_list = sorted(list(set(map_list)))
        np_map = np.array(map_list)
        np_map = np_map.reshape(size,size)
        tmp_mean = []
        self.team_count = []
        self.nearest_unit = []
        for i in range(max(unit_list)//100+1):
            tmp_unit_loc = np.where((np_map > i*100)&(np_map <= (i+1)*100))
            self.team_count.append(len(tmp_unit_loc[0]))
            tmp_list = np.array(list(zip(tmp_unit_loc[1],tmp_unit_loc[0])))
            if i>0:
                self.nearest_unit = self.nearest_unit+list(zip(tmp_unit_loc[1],tmp_unit_loc[0]))
            self.unit_loc.append([tmp_list,np_map[tmp_unit_loc]])
            tmp_mean.append(tmp_list.mean(0))            
        self.own_loc = tmp_mean[0]
        for num,elem in enumerate(tmp_mean[1:]):
            self.dist_sorted.append([(((tmp_mean[0] - elem)**2).sum())**0.5,num,elem.tolist(),self.team_count[num+1]])
        def sort_key(elem):
            return elem[0]
        def sort_key2(elem):
            return elem[2]
        if len(self.nearest_unit)>0:
            self.dist_sorted.sort(key=sort_key)
            self.nearest_unit = list(zip(((((np.array(self.nearest_unit) - tmp_mean[0])**2).sum(1))**0.5).tolist(),self.nearest_unit))
            self.nearest_unit.sort(key=sort_key)
        return

    def run_away(self,enemy_team_num = 1):
        self.unit_loc_inf()
        if len(self.dist_sorted)>enemy_team_num:
            self.keyborad_operate('esc')
            self.mouse_operate(519,450,'left')
            time.sleep(1)
            self.mouse_operate(519,450,'left')
            return True
        return False

#之后将全面重写
class soldier_behavior(Gersang_window):
    def all_hold(self,unit_button = '0'):
        self.keyborad_operate(unit_button)
        self.keyborad_operate('h')
        time.sleep(0.1)

    def all_stop(self,unit_button = '0'):
        self.keyborad_operate(unit_button)
        self.keyborad_operate('s')
        time.sleep(0.1)

    def summoner_unit(self,skill_button,enemy_num,distance = 0.5,unit_num = 1,unit_button = 1):
        #unit_button = 该单位设定的快捷键 skill_button = 释放技能的快捷键 enemy_num = 要朝着第几近的敌人释放
        num = min(enemy_num,len(self.dist_sorted)-1)
        x,y = self.dist_sorted[num][2]
        self.complex_operation(x,y,skill_button,'ctrl_left',distance = distance)
        time.sleep(0.1)
        return

    def buffer_unit(self,skill_button,enemy_num,distance = 0.5,unit_num = 1,unit_button = 1):
        #unit_button = 该单位设定的快捷键 skill_button = 释放技能的快捷键 
        self.complex_operation(self.own_loc[0],self.own_loc[1],skill_button,'ctrl_left') 
        time.sleep(0.1)
        return

    def unit_transform(self,skill_button,enemy_num,distance = 0.5,unit_num = 1,unit_button = 1):
        self.keyborad_operate(skill_button)
        time.sleep(0.1)
        return

    def debuffer_unit(self,skill_button,enemy_num,distance = 0.5,unit_num = 1,unit_button = 1):
        for num,target in enumerate(self.dist_sorted):
            x,y = target[2]
            self.complex_operation(x,y,skill_button,'ctrl_left',distance = distance)
            if num>2:
                break
        time.sleep(0.1)
        return

    def main_attaker(self,skill_button,enemy_num,distance = 2,unit_num = 1,unit_button = 1):
        while len(self.nearest_unit)>0:         
            if dm.ReadInt(self.hwnd_num,'0237556C',1)!=unit_num:
                self.keyborad_operate(unit_button)
            #target_num = min(random.randint(0,1),len(self.nearest_unit)-1)
            x,y = self.nearest_unit[0][1]
            self.complex_operation(x,y,skill_button,'left',distance = distance)
            time.sleep(1.5)
            self.unit_loc_inf()
        return

    def a_skill(self,skill_button,enemy_num,distance = 0.75,unit_num = 1,unit_button = 1):
        num = min(enemy_num,len(self.dist_sorted)-1)
        x,y = self.dist_sorted[num][2]
        self.complex_operation(x,y,skill_button,'left','ctrl',distance = distance)
        time.sleep(0.1)
        return

    def go_back(self,unit_button):
        self.keyborad_operate(unit_button)
        self.complex_operation(self.own_loc[0],self.own_loc[1],None,'ctrl_right') 
        self.keyborad_operate('s','ctrl')
        time.sleep(0.1)
        return

class log_info():
    def __init__(self, play_name):
        self.play_name = play_name
        if not os.path.exists('./log_fight.txt'):
            with open('./log_fight-{}.json'.format(self.play_name),mode = 'w') as f:
                f.write(json.dumps({self.now_time():0}))
    def log_fight_info(self):
        with open('./log_fight-{}.json'.format(self.play_name),mode = 'r') as f:
            json_inf = json.loads(f.read())
            now = self.now_time()
            json_inf[now] = json_inf.get(now, 0) + 1
            print(json_inf)
            with open('./log_fight-{}.json'.format(self.play_name),mode = 'w') as f:
                f.write(json.dumps(json_inf))
    def now_time(self):
        return time.strftime("%Y-%m-%d", time.localtime())

class role_behavior(soldier_behavior):
    def gersang_loop(self,a_player):
        self.player_behavior = a_player[2].strip()
        monster_name = a_player[1].strip()
        food_carryer = a_player[4].strip()
        self.need_run_away = int(a_player[5].strip())
        while True:
            if self.check_fight() is False:
                self.take_food(food_carryer)
                self.find_monster(*monster_info[monster_name])
                self.fight()
                self.log.log_fight_info()
        return

    def fight(self):
        behavior_dist = {'增益':self.buffer_unit,'召唤':self.summoner_unit,'变身':self.unit_transform,'减益':self.debuffer_unit,'主攻':self.main_attaker,'组合':self.a_skill}
        behavior_count = {'增益':0,'召唤':0,'变身':0,'减益':0,'主攻':0,'组合':0}
        pre_unit = -1
        self.all_stop()
        behaviors_list = re.split('\r\n',self.player_behavior)
        if self.need_run_away:
            if self.run_away(self.need_run_away):
                while self.check_fight() is True:
                    time.sleep(0.1)
                return
        for num,a_behavior in enumerate(behaviors_list):
            self.unit_loc_inf()
            now_behavior = re.split(' ',a_behavior)
            behavior_name = now_behavior[0]
            skill_button = now_behavior[1]
            unit_button = now_behavior[2]
            if len(now_behavior)>3:
                skill_distance = int(now_behavior[3])
            if pre_unit!= unit_button:
                if num>0:
                    self.go_back(pre_unit)
                self.keyborad_operate(unit_button)
                unit_num = dm.ReadInt(self.hwnd_num,'0237556C',1)
            if len(now_behavior)>3:
                behavior_dist[behavior_name](skill_button,behavior_count[behavior_name],skill_distance,unit_num=unit_num,unit_button=unit_button)
            else:
                behavior_dist[behavior_name](skill_button,behavior_count[behavior_name],unit_num=unit_num,unit_button=unit_button)
            behavior_count[behavior_name] = behavior_count[behavior_name]+1
            pre_unit = unit_button
        while self.check_fight() is True:
            time.sleep(0.1)

class ming_nv_behavior(soldier_behavior):
    account = '157204835'
    password = 'zhanghao06'
    food_carryer = '1'

    def gersang_loop(self,monster_name):
        while True:
            if self.check_fight() is False:
                self.take_food(self.food_carryer)
                self.find_monster(*monster_info[monster_name])
                self.fight()
                self.log.log_fight_info()
        return

    def fight(self):
        self.all_stop()
        self.li_ling()
        self.angel()
        self.unit_loc_inf()
        self.player()
        x1,y1 = self.beng_yuan_shi()
        #self.player_in_map(x1,y1)
        x2,y2 = self.a_mo()
        #self.player_in_map(x2,y2)
        self.lian_li()
        self.angel()
        self.mouse_operate(200,200)
        while self.check_fight() is True:
            time.sleep(0.1)

class tai_nan_behavior(soldier_behavior):
    account = 'xyzwq1106'
    password = 'zhanghao..06'
    food_carryer = '='

    def gersang_loop(self,monster_name):
        while True:
            if self.check_fight() is False:
                self.take_food(self.food_carryer)
                self.find_monster(*monster_info[monster_name])
                self.fight()
                self.log.log_fight_info()
        return

    def fight(self):
        self.all_stop()
        self.unit_loc_inf()
        if self.run_away(1) is False:
            self.taiwan_player()
            self.feng_huang()
            self.hu_tian()
            self.mouse_operate(200,200)
        while self.check_fight() is True:
            time.sleep(0.1)

def player_thread(hwnd_num,a_player,player_num):
    behavior_list = [tai_nan_behavior,ming_nv_behavior]
    player_name = a_player[0].strip()
    monster_name = a_player[1].strip()
    log = log_info(player_name)
    window = role_behavior(hwnd_num,log)
    manager_dict[hwnd_num]['mem_loc'] = find_mem_loc(hwnd_num,*monster_info[monster_name])
    window.gersang_loop(a_player)
    return

def guaji():
    global manager_dict
    manager_dict = {}
    one_hwnd = dm.FindWindow("","Gersang") 
    manager_dict[one_hwnd] = {'mem_loc':0,'is_fight':False}
    config = codecs.open('.\config.txt','r+',encoding='utf-8').read()
    config = re.split('=====',config)
    for  num,text in enumerate(config):
        config[num] = re.split('----',text)
    play_str = ','.join([str(num+1)+':'+text[0].strip() for num,text in enumerate(config)])
    play_num = input('是什么角色?请输入序号'+play_str)
    dm.SetWindowState(one_hwnd,1)
    player_thread(one_hwnd,config[int(play_num)-1],play_num)

    

if __name__=="__main__":
    guaji()