import copy

class LowestLevelAlgorithm(object):
    
    def __init__(self,node_weight,XB_size):
        '''
        node_weight: 字典形式，片上的块为切分之后的块大小。
                        key为所有需要进行排布的节点名称，
                        value为含有两个元素的列表，第一个元素为宽，第二个元素为高，
                        （卷积核需要按照片上部署的方式展开）。
        XB_size: 单个计算阵列的大小，第一个元素为宽，第二个元素为高。
        '''
        self.node_weight = node_weight
        self.XB_size = XB_size
    
    def run(self):
        """
        lowest_level_algorithm for placement
        return:
            按照水平线进行排布的所有节点的位置信息，列表形式
        """
        node_list = copy.deepcopy(list(self.node_weight.keys()))
        # 按照节点宽度排序
        node_list = self.node_sort(node_list)
        
        XB_szie = self.XB_size
        all_node_list = []
        while node_list:
            lowest_level = {}
            cross_part_level = {}
            # 初始化水平线
            # [W_start, W, H]
            lowest_level["1"] = [0, XB_szie[0], XB_szie[1]]
            
            same_chip = []
            l = copy.deepcopy(node_list)
            for node_name in l:
                # print(node_name)
                # 更新当前的水平线，包括两部分：lowest_level 与 cross part level
                lowest_level_all = copy.deepcopy(lowest_level)
                lowest_level_all.update(cross_part_level)
                
                for level_key, level_value in lowest_level_all.items():
                    
                    if (self.node_weight[node_name][0] <= level_value[1] - level_value[0]) and (self.node_weight[node_name][1] <= level_value[2]):
                        node_address = {}
                        sx = level_value[0] 
                        sy = self.XB_size[1] - level_value[2]
                        w = self.node_weight[node_name][0]
                        h = self.node_weight[node_name][1]
                        address = [sx,sy,h,w] # 列起始地址,行起始地址,行数,列数
                        #更新lowest_level
                        lowest_level, cross_part_level = self.update_level(level_key,address,lowest_level)
                        node_address[node_name] = [sy,sx,h,w]
                        same_chip.append(node_address)
                        node_list.remove(node_name)
                        break  
                # print(level_key)
                # print(same_chip)
                # print(lowest_level)
                # print(cross_part_level)
                # input()
            all_node_list.append(same_chip)
            
        return all_node_list    
        
    def update_level(self, level_key, address, lowest_level):
        '''
        按照最低水平线更新布局空间
        '''
        
        new_level = {}
        
        if level_key not in lowest_level.keys():
            
            h_min = 0 # 记录最低点
            c = 0 # 记录拆分
            
            for level_key, level_value in lowest_level.items():
                
                #    
                if address[0] == level_value[0]:
                    new_level[level_key] = [address[0], level_value[1], level_value[2]-address[2]]
                    h_min = level_value[2]-address[2]
                
                elif address[0] + address[3] <= level_value[1]:
                    new_level[level_key] = [level_value[0], address[0] + address[3], h_min]
                    if address[0] + address[3] < level_value[1]:
                        new_level[len(lowest_level.keys() + c)] = [address[0]+address[3], level_value[1], h_min]
                        c += 1
                    # h_min = level_value[2]-address[2]
                else:
                    new_level[level_key] = level_value
                
        else:
            s_num = int(level_key)
            for level_key, level_value in lowest_level.items():
                if int(level_key) < s_num:
                    new_level[level_key] = level_value
                elif int(level_key) == s_num:
                    new_level[level_key] = [address[0], address[0]+address[3], level_value[2]-address[2]]
                    if address[0] + address[3] <= level_value[1]:
                        new_level[str(s_num+1)] = [address[0]+address[3], level_value[1], level_value[2]]
                else:
                    new_level[str(int(level_key)+1)] = level_value
        
        # 消除冗余与 合并
        new_level = self.remove(new_level)
        
        # 增加new_level中的空白交叠部分
        cross_part_level = self.create_cross_part(new_level)
        
        return new_level, cross_part_level
    
    
    def remove(self, level):
        
        c = 1
        new_level = {}
        same_h = {}
        # 消除冗余
        for key, value in level.items():
            if value[0] != value[1]:
                new_level[str(c)] = value
                c += 1
            if value[2] not in same_h:
                same_h[value[2]] = []
            
            same_h[value[2]].append(str(c-1))
        # print(new_level)
        # 合并
        for k,v in same_h.items():
            len_ = len(v)
            if len_ != 1:
                re_ = []
                for i in range(len_):
                    value_1 = new_level[v[i]]
                    for j in range(i+1, len_):
                        value_2 = new_level[v[j]]
                        if value_1[1] == value_2[0]:
                            new_level[v[j]] = [value_1[0], value_2[1], value_2[2]]
                            re_.append(v[i])
                            break
                for i in re_:
                    new_level.pop(i)
        
        new_level_ = {}
        # 重新排序
        c = 0
        for k,v in new_level.items():
            new_level_[str(c)] = v
            c += 1
            
        return new_level_
    
    def create_cross_part(self, level):
        '''
        产生 空白部分的 交叉区域
        '''
        new_level = {}
        # 获取key列表
        key_list = list(level.keys())
        len_ = len(key_list)
        
        c = 1
        # 从level中的第一个区域 开始依次寻找 后面的空白交叉区域 
        for i in range(len_):
            level1 = level[key_list[i]]
            for j in range(i+1,len_):
                level2 = level[str(key_list[j])]
                # 判断依据是 第一个区域的列最后一个坐标 与 第二区域的列开始坐标一致
                if level1[1] == level2[0]:
                    new_level[str(int(key_list[-1]) + c)] = [level1[0], level2[1], min(level1[2], level2[2])] 
                    c += 1
        return new_level
    
    def node_sort(self,conv_node):
        '''
        按照权重的W大小进行节点排序，越大越靠前
        '''
        # 按照output大小进行排序
        for i in range(len(conv_node)):
            for j in range(len(conv_node)-1,i,-1):
                if self.node_weight[conv_node[j-1]][0] < self.node_weight[conv_node[j]][0] :
                    t = conv_node[j]
                    conv_node[j] = conv_node[j-1]
                    conv_node[j-1] = t
        return conv_node