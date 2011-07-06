#!/usr/bin/python -i

# abaqus2dyna.by
# 
# Copyright 2011 Tim Hartman <tbhartman@gmail.com>
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

version='0.0.1'

import argparse
import numpy as np
import re
from collections import *
import datetime

# argument parsing definitions

parser = argparse.ArgumentParser(prog='abaqus2dyna',
                                 description='Translate Abaqus to LS-DYNA')
parser.add_argument('input',
                    metavar='INPUT',
                    help='Abaqus keyword file (limit one)',
                    nargs=1,
                    type=argparse.FileType('r'))
parser.add_argument('-o, --output',
                    dest='output',
                    metavar='OUTPUT',
                    help='LS-DYNA keyword file output location',
                    type=argparse.FileType('w'))
parser.add_argument('-v, --version',
                    action='version',
                    version='%(prog)s ' + version)
args = parser.parse_args()

# class definitions

class Element():
    id = 0
    type = None
    
    def __init__(self):
        self.node = []

class Node():
    id = 0
    pos = None

    def __init__(self):
        self.pos = np.zeros(3)

class Part():
    id = 0

class Set(list):
    name = None
    instance = None

class AbaqusPart(Part):
    def __init__(self, name):
        self.name = name
        self.element = {}
        self.node = {}

class AbaqusInstance():
    name = None
    part = None
    translation = None
    rotation = None
    
    @property
    def rotation_matrix(self):
        th = self.rotation['deg']
        a = self.rotation['a']
        b = self.rotation['b']
        ux = b[0] - a[0]
        uy = b[1] - a[1]
        uz = b[2] - a[2]
        rm = np.ndarray([3,3])
        th = th * np.pi/180.
        cos = np.cos(th)
        sin = np.sin(th)
        one_cos = 1-cos
        rm[0,0] = cos + ux**2*one_cos
        rm[0,1] = ux*uy*one_cos - uz*sin
        rm[0,2] = ux*uz*one_cos + uy*sin
        rm[1,0] = uy*ux*one_cos + uz*sin
        rm[1,1] = cos + uy**2*one_cos
        rm[1,2] = uy*uz*one_cos - ux*sin
        rm[2,0] = uz*ux*one_cos - uy*sin
        rm[2,1] = uz*uy*one_cos + ux*sin
        rm[2,2] = cos + uz**2*one_cos
        return rm
    
    def __init__(self):
        self.translation = np.zeros(3)
        self.rotation = {}
        self.rotation['a'] = np.zeros(3)
        self.rotation['b'] = np.zeros(3)
        self.rotation['deg'] = 0


class AbaqusInput():
    def __init__(self):
        self.part = {}
        self.instance = {}
        self.count = Counter()
        self.set = {}
        self.set['node'] = {}
        self.set['element'] = {}

# parse Abaqus input file

def ParseAbaqus(file):
    ret = AbaqusInput()
    count = Counter()

    regex = {}
    regex['comment'] = re.compile(r'^\*\*')
    regex['keyword'] = re.compile(r'^\*[a-zA-Z0-9 ]+[,\n]')
    regex['data'] = re.compile(r'^(?!\*)')
    
    def ends_at(kw,loc):
        if loc == '*':
            if section[len(section)-1] != kw:
                section.pop(section.index(kw))
        if type(loc) is int:
            if count['keyword_line'] == loc:
                section.pop(section.index(kw))
        if type(loc) is str:
            if loc in section:
                section.pop(section.index(kw))

    for line in file:
        current_instance = None
        ret.count['line'] += 1
        if regex['comment'].search(line):
            # This is a comment line
            ret.count['comment'] += 1
            continue
        if regex['keyword'].search(line):
            match = regex['keyword'].search(line) 
            # This is a keyword line
            ret.count['keyword'] += 1
            kw = match.group(0).upper().strip(' ,\n*')
            ret.count['*' + kw] += 1
            count['keyword_line'] = 0
            # parse keyword arguments
            kwargs = {}
            splitline = line.split(',')
            splitline.pop(0)
            for i in splitline:
                i = i.strip(' \n')
                if '=' in i:
                    i = i.split('=')
                    kwargs[i[0]] = i[1].strip('\'\"')
                else:
                    kwargs[i] = True
            #print('{:5d}:{:15s}'.format(ret.count['line'],kw))
            #if len(kwargs) > 0:
                #print(kwargs)


        if regex['data'].search(line):
            count['keyword_line'] += 1
        
        # from here on, process the current keyword
        
        if kw == 'PART':
            if count['keyword_line'] == 0:
                name = kwargs['name']
                ret.part[name] = AbaqusPart(name)
                current_part = name
        if kw == 'END PART':
            current_part = None
        if kw == 'ASSEMBLY':
            in_assembly = True
        if kw == 'END ASSEMBLY':
            in_assembly = False
        if kw == 'INSTANCE':
            if count['keyword_line'] == 0:
                instance = AbaqusInstance()
                instance.name = kwargs['name']
                instance.part = kwargs['part']
                current_instance = instance.name
                ret.instance[instance.name] = instance
            if count['keyword_line'] == 1:
                parts = line.split(',')
                instance.translation[:] = parts
            if count['keyword_line'] == 2:
                parts = line.split(',')
                instance.rotation['a'][:] = parts[0:3]
                instance.rotation['b'][:] = parts[3:6]
                instance.rotation['deg'] = float(parts[6])
        if kw == 'END INSTANCE':
            current_instance = None
        if kw == 'NODE':
            #import pdb; pdb.set_trace()
            if count['keyword_line'] > 0:
                parts = line.split(',')
                node = Node()
                node.id = int(parts[0])
                node.pos[0] = float(parts[1])
                node.pos[1] = float(parts[2])
                try:
                    node.pos[2] = float(parts[3])
                except:
                    pass
                ret.part[current_part].node[node.id] = node
        if kw == 'ELEMENT':
            if count['keyword_line'] > 0:
                parts = line.split(',')
                element = Element()
                element.id = int(parts[0])
                for i in range(1,len(parts)):
                    element.node.append(int(parts[i]))
                element.type = kwargs['type']
                ret.part[current_part].element[element.id] = element
        if kw == 'ELSET':
            #import pdb; pdb.set_trace()
            if 'instance' in kwargs:
                if count['keyword_line'] == 0:
                    elset = Set()
                    elset.name = kwargs['elset']
                    elset.instance = kwargs['instance']
                    ret.set['element'][elset.name] = elset
                if count['keyword_line'] > 0:
                    parts = line.split(',')
                    try:
                        if kwargs['generate']:
                            start = int(parts[0])
                            stop = int(parts[1]) + 1
                            inc = int(parts[2])
                            for i in range(start, stop, inc):
                                elset.append(i)
                    except:
                        for i in parts:
                            elset.append(int(i))


    return ret
        
inp = ParseAbaqus(args.input[0])
#print(inp.count)



# finally, output dyna keyword

def WriteDynaFromAbaqus(abaqus_keyword, output_filename):
    inp = abaqus_keyword
    output = {}
    output['header'] = (
        '$ LS-DYNA keyword input file\n' + 
        '$ Auto-translated from ' + args.input[0].name +
            ' by abaqus2dyna.py\n')
    output['timestamp'] = ('$ translated at: ' +
        datetime.datetime.utcnow().strftime("%y-%m-%d %H:%M:%S UTC") + '\n')
    output['data'] = ''
    output['stats'] = {}
    output['stats']['pid'] = []
    output['stats']['esid'] = []
    output['stats']['nsid'] = []

    def comment_line(string, fill=''):
        return ('${:' + fill + '^78s}$\n').format(string)
    set_comment_sep = comment_line('',fill='-')
    set_comment_fmt = '${:>12s}{:12d}' + ' '*12 + '{:42s}$\n'
    set_comment_head = ('${:_>12s}{:_>12s}'+'_'*12 + '{:_<42s}$\n'
        ).format('type','id','name')
    output['sep'] = comment_line('',fill='*')
    
    count = Counter()
    offset = Counter()
    
    # need to write nodes, then elements, then sets
    for i in inp.instance:
        count['part'] += 1
        instance = inp.instance[i]
        rotation_matrix = instance.rotation_matrix
        output['stats']['pid'].append([count['part'],instance.name])
        # write nodes
        offset['node'] = count['node']
        offset['element'] = count['element']
        #import pdb; pdb.set_trace()
        if inp.part[instance.part].node:
            output['data'] += '*NODE\n'
            node_fmt = '{0:8d}{1[0]:16.7e}{1[1]:16.7e}{1[2]:16.7e}\n'
            for j in inp.part[instance.part].node:
                node = inp.part[instance.part].node[j]
                id = node.id + offset['node']
                orig_pos = node.pos
                final_pos = rotation_matrix.dot(orig_pos) #rotation
                final_pos += instance.translation #translation
                output['data'] += node_fmt.format(id,final_pos)
                count['node'] += 1
        element_conversion = {'C3D8R':'SOLID',
                              'S4R':'SHELL'}
        if inp.part[instance.part].element:
            current_type = None
            element_fmt = '{:8d}{:8d}{:8d}{:8d}{:8d}{:8d}{:8d}{:8d}{:8d}{:8d}\n'
            for j in inp.part[instance.part].element:
                element = inp.part[instance.part].element[j]
                if element.type != current_type:
                    output['data'] += '*ELEMENT_' + element_conversion[element.type] + '\n'
                    current_type = element.type
                id = element.id + offset['element']
                nodes = (np.array(element.node) + offset['node']).tolist()
                for k in range(8 - len(nodes)):
                    nodes.append(0)
                #import pdb; pdb.set_trace()
                output['data'] += element_fmt.format(id,count['part'],*nodes)
                count['element'] += 1
        # sets
        for k in inp.set['element']:
            if inp.set['element'][k].instance == instance.name:
                #TODO, need to check that all elements are same type (for DYNA sake)
                start = True
                set_naming_parts = k.split(':')
                set_name = set_naming_parts[1]
                set_id = int(set_naming_parts[0][1:])
                tmp_element_count = 0
                for m in inp.set['element'][k]:
                    if start:
                        element = inp.part[instance.part].element[m]
                        output['data'] += '*SET_' + element_conversion[element.type] + '\n'
                        output['data'] += '{:10d}\n'.format(set_id)
                        start = False
                    output['data'] += '{:10d}'.format(m + offset['element'])
                    tmp_element_count += 1
                    if tmp_element_count > 7:
                        output['data'] += '\n'
                if tmp_element_count <= 7:
                    output['data'] += '\n'
                count['elset'] += 1
                output['stats']['esid'].append([set_id,set_name])
        for k in inp.set['node']:
            if inp.set['node'][k].instance == instance.name:
                #TODO, need to check that all elements are same type (for DYNA sake)
                start = True
                set_naming_parts = k.split(':')
                set_name = set_naming_parts[1]
                set_id = int(set_naming_parts[0][1:])
                tmp_node_count = 0
                for m in inp.set['element'][k]:
                    if start:
                        output['data'] += '*SET_NODE\n'
                        output['data'] += '{:10d}\n'.format(set_id)
                        start = False
                    output['data'] += '{:10d}'.format(m + offset['node'])
                    tmp_node_count += 1
                    if tmp_node_count > 7:
                        output['data'] += '\n'
                if tmp_node_count <= 7:
                    output['data'] += '\n'
                count['nodeset'] += 1
                output['stats']['nsid'].append([set_id,set_name])
        
    
    dyna_string = output['header']
    dyna_string += output['timestamp']
    dyna_string += output['sep']
    # statistics
    dyna_string += comment_line('Model Stats')
    dyna_string += set_comment_head
    for i in output['stats']:
        for j in output['stats'][i]:
            dyna_string += set_comment_fmt.format(i,j[0],j[1])
        dyna_string += set_comment_sep
    dyna_string += output['sep'] + output['data']

    k = open(output_filename, 'w')
    k.write(dyna_string)
    k.close()
    return


WriteDynaFromAbaqus(inp, args.input[0].name + '.k')



    
