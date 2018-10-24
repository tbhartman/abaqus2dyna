#!/usr/bin/python3
import argparse
import collections
import datetime
import re
import sys
import tempfile

import numpy as np

class Model:
    def __init__(self):
        self.assembly = None

    @staticmethod
    def parse(cls, file_or_name):
        NotImplemented()
    def write(cls, file_or_name):
        NotImplemented()

class Assembly:
    def __init__(self):
        self.name = None
        self.instances = []
        self.sets = {}

class Instance:
    def __init__(self):
        self.name = None
        self.part = None
        self.translation = None
        self.rotation = None

class Part:
    def __init__(self):
        self.name = None
        self.nodes = None
        self.elements = None
        self.sets = None

class AbaqusInput:
    def __init__(self):
        self.assembly = None
        self.header = None

    @staticmethod
    def parse(cls, file_or_name):
        ret = cls()
        return ret


class Orientation():
    system = None
    a = None
    b = None
    c = None
    rot_axis = None
    rot = None

    def __init__(self):
        self.a = np.empty(3)
        self.a.fill(np.nan)
        self.b = np.empty(3)
        self.b.fill(np.nan)
        self.c = np.empty(3)
        self.c.fill(0)


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

class Section():
    elset = None
    orientation = None

class Part():
    id = 0

class Set(list):
    name = None
    instance = None
    part = None

class AbaqusPart(Part):
    orientation = None
    set = None
    section = None

    def __init__(self, name):
        self.name = name
        self.element = {}
        self.node = {}
        self.set = {}
        self.set['node'] = {}
        self.set['element'] = {}
        self.section = []
        self.orientation = {}

def GetRotationMatrix(a,b,th):
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
        rm = GetRotationMatrix(a,b,th)
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
        self.count = collections.Counter()
        self.set = {}
        self.set['node'] = {}
        self.set['element'] = {}

# parse Abaqus input file

def ParseAbaqus(file):
    ret = AbaqusInput()
    count = collections.Counter()

    regex = {}
    regex['comment'] = re.compile(r'^\*\*')
    regex['keyword'] = re.compile(r'^\*[a-zA-Z0-9 ]+[,\n]')
    regex['data'] = re.compile(r'^(?!\*)')

    line_counter = collections.Counter()
    line_counter['total'] = len(file.readlines())
    file.seek(0)

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

    def update_term(complete=False):
        total = line_counter['total']
        count = line_counter['current']
        perc = int(100 * count * 1.0 / total)
        old_perc = int(100 * (count-1)*1.0/total)
        if perc != old_perc or count == 1 or perc == 1:
            perc = count * 1.0 / total
            #import pdb; pdb.set_trace()
            fmt = 'Parsing ({:3.0f}% complete)'.format(100*perc)
            if complete:
                to_write = fmt + '...done!\n'
                sys.stdout.write(to_write)
            else:
                to_write = fmt + '\r'
                sys.stdout.write(to_write)
                sys.stdout.flush()

    for line in file:
        line_counter['current'] += 1
        update_term()
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
        if kw == 'ORIENTATION':
            if count['keyword_line'] == 0:
                orient = Orientation()
                orient.name = kwargs['name']
                if 'system' in kwargs:
                    orient.system = kwargs['system']
                else:
                    orient.system = 'RECTANGULAR'
                ret.part[current_part].orientation[orient.name] = orient
            elif count['keyword_line'] == 1:
                parts = line.split(',')
                orient.a[:] = parts[0:3]
                orient.b[:] = parts[3:6]
                if len(parts) == 9:
                    orient.c[:] = parts[6:9]
            elif count['keyword_line'] == 2:
                parts = line.split(',')
                orient.rot_axis = int(parts[0])
                orient.rot = float(parts[1])
        if 'SECTION' in kw:
            if count['keyword_line'] == 0 and 'orientation' in kwargs:
                section = Section()
                section.elset = kwargs['elset']
                section.orientation = kwargs['orientation']
                ret.part[current_part].section.append(section)
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
            if count['keyword_line'] == 0:
                elset = Set()
                elset.name = kwargs['elset']
                if 'instance' in kwargs:
                    elset.instance = kwargs['instance']
                    ret.set['element'][elset.name] = elset
                else:
                    elset.part = current_part
                    ret.part[current_part].set['element'][elset.name] = elset

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
        if kw == 'NSET':
            if count['keyword_line'] == 0:
                nset = Set()
                nset.name = kwargs['nset']
                if 'instance' in kwargs:
                    nset.instance = kwargs['instance']
                    ret.set['node'][nset.name] = nset
                else:
                    nset.part = current_part
                    ret.part[current_part].set['node'][nset.name] = nset

            if count['keyword_line'] > 0:
                parts = line.split(',')
                try:
                    if kwargs['generate']:
                        start = int(parts[0])
                        stop = int(parts[1]) + 1
                        inc = int(parts[2])
                        for i in range(start, stop, inc):
                            nset.append(i)
                except:
                    for i in parts:
                        nset.append(int(i))

    update_term(True)
    #import pdb; pdb.set_trace()
    return ret

def WriteDynaFromAbaqus(total_nodel, inp_name, abaqus_keyword, ostream):
    #global total_nodel
    written_nodel = 0
    def update_term(complete=False):
        #global total_nodel
        #global ostream
        total = total_nodel
        counted = count['node'] + count['element']
        perc = int(1000 * counted * 1.0 / total)
        old_perc = int(1000 * (counted-1)*1.0/total)
        if perc != old_perc or counted == 1:
            status = 'Compiling data ({:5.1f}% complete)'.format(perc/10)
            if complete:
                to_write = status + '...done\n'
            else:
                to_write = status + '\r'
            sys.stdout.write(to_write)
            sys.stdout.flush()

    inp = abaqus_keyword
    output = {}
    output['header'] = (
        '$ LS-DYNA keyword input file\n' +
        '$ Auto-translated from ' + inp_name +
            ' by abaqus2dyna.py\n')
    output['timestamp'] = ('$ translated at: ' +
        datetime.datetime.utcnow().strftime("%y-%m-%d %H:%M:%S UTC") + '\n')
    output['data'] = tempfile.TemporaryFile(mode='w+')
    output['stats'] = {}
    output['stats']['pid'] = []
    output['stats']['esid'] = []
    output['stats']['nsid'] = []

    def comment_line(string, fill='', newline=True):
        ret = ('${:' + fill + '^78s}$').format(string)
        if newline:
            ret += '\n'
        return ret
    set_comment_sep = comment_line('',fill='-')
    set_comment_fmt = '${:>12s}{:12d}' + ' '*12 + '{:42s}$\n'
    set_comment_head = ('${:_>12s}{:_>12s}'+'_'*12 + '{:_<42s}$\n'
        ).format('type','id','name')
    output['sep'] = comment_line('',fill='*')

    count = collections.Counter()
    offset = collections.Counter()

    # need to write nodes, then elements, then sets
    for i in inp.instance:
        #print('Writing instance ' + i)
        count['part'] += 1
        output['data'].write(comment_line('',fill='*'))
        output['data'].write(comment_line('Data for part ' + i + ', pid=' + str(count['part'])))
        output['data'].write(comment_line('',fill='*'))
        instance = inp.instance[i]
        rotation_matrix = instance.rotation_matrix
        output['stats']['pid'].append([count['part'],instance.name])
        # write nodes
        offset['node'] = count['node']
        offset['element'] = count['element']
        #import pdb; pdb.set_trace()
        if inp.part[instance.part].node:
            output['data'].write('*NODE\n')
            node_fmt = '{0:8d}{1[0]:16.8e}{1[1]:16.8e}{1[2]:16.8e}\n'
            for j in inp.part[instance.part].node:
                node = inp.part[instance.part].node[j]
                id = node.id + offset['node']
                orig_pos = node.pos
                final_pos = rotation_matrix.dot(orig_pos) #rotation
                final_pos += instance.translation #translation
                output['data'].write(node_fmt.format(id,final_pos))
                count['node'] += 1
                update_term()
        element_conversion = {'C3D8R':'SOLID',
                              'S4R':'SHELL'}
        if inp.part[instance.part].element:
            current_type = None
            current_has_orient = None
            element_fmt = '{:8d}{:8d}{:8d}{:8d}{:8d}{:8d}{:8d}{:8d}{:8d}{:8d}\n'
            for j in inp.part[instance.part].element:
                element = inp.part[instance.part].element[j]
                id = element.id + offset['element']
                this_has_orient = False
                this_orient = None
                if element_conversion[element.type] == 'SOLID':
                    for k in inp.part[instance.part].section:
                        if element.id in inp.part[instance.part].set['element'][k.elset]:
                            this_has_orient = True
                            this_orient = inp.part[instance.part].orientation[k.orientation]
                            continue
                if element.type != current_type or this_has_orient != current_has_orient:
                    output['data'].write('*ELEMENT_' + element_conversion[element.type])
                    if this_has_orient:
                        output['data'].write('_ORTHO')
                    output['data'].write('\n')
                    current_type = element.type
                    current_has_orient = this_has_orient

                nodes = (np.array(element.node) + offset['node']).tolist()
                for k in range(8 - len(nodes)):
                    nodes.append(0)
                #import pdb; pdb.set_trace()
                output['data'].write(element_fmt.format(id,count['part'],*nodes))
                if current_has_orient:

                    a = np.empty(3)
                    d = np.empty(3)
                    # get element centroid
                    centroid = np.zeros(3)
                    for k in element.node:
                        centroid += inp.part[instance.part].node[k].pos
                    centroid /= len(nodes)
                    system = this_orient.system
                    if system == 'CYLINDRICAL':
                        #import pdb; pdb.set_trace()
                        c = this_orient.b - this_orient.a
                        c /= np.linalg.norm(c)
                        g = centroid - this_orient.a # to centroid from a
                        h = c.dot(g) # distance along _ab_ to centroid
                        h = this_orient.a + h*c # vector along _ab_ to centroid
                        a = centroid - h
                        a /= np.linalg.norm(a)
                        d = np.cross(c,a)
                        # maybe an additional rotation?
                        if this_orient.rot_axis == 1:
                            axis_point = a
                        elif this_orient.rot_axis == 2:
                            axis_point = d
                        else:
                            axis_point = c
                        rotation_matrix = GetRotationMatrix([0,0,0],axis_point,this_orient.rot)
                        a = rotation_matrix.dot(a)
                        d = rotation_matrix.dot(d)
                        # rotate local CS with instance
                        rotation_matrix = instance.rotation_matrix
                        a = rotation_matrix.dot(a) #rotation
                        #a += instance.translation #translation
                        d = rotation_matrix.dot(d) #rotation
                        #d += instance.translation #translation
                        d /= np.linalg.norm(d)
                        a /= np.linalg.norm(a)
                        #import pdb; pdb.set_trace()
                    if system in ['RECTANGULAR',None]:
                        a = this_orient.a
                        a /= np.linalg.norm(a)
                        b = this_orient.b
                        b /= np.linalg.norm(b)
                        c = np.cross(a,b)
                        d = np.cross(c,a)
                        # maybe an additional rotation?
                        if this_orient.rot_axis == 1:
                            axis_point = a
                        elif this_orient.rot_axis == 2:
                            axis_point = d
                        else:
                            axis_point = c
                        rotation_matrix = GetRotationMatrix([0,0,0],axis_point,this_orient.rot)
                        a = rotation_matrix.dot(a)
                        d = rotation_matrix.dot(d)
                        # rotate local CS with instance
                        rotation_matrix = instance.rotation_matrix
                        a = rotation_matrix.dot(a) #rotation
                        #a += instance.translation #translation
                        d = rotation_matrix.dot(d) #rotation
                        #d += instance.translation #translation
                        d /= np.linalg.norm(d)
                        a /= np.linalg.norm(a)
                        #import pdb; pdb.set_trace()
                    else:
                        raise Exception('yep, ' + system + ' not yet implemented')
                    output['data'].write('{0[0]:16.7e}{0[1]:16.7e}{0[2]:16.7e}\n'.format(a))
                    output['data'].write('{0[0]:16.7e}{0[1]:16.7e}{0[2]:16.7e}\n'.format(d))
                count['element'] += 1
                update_term()
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
                        output['data'].write('*SET_' + element_conversion[element.type] + '\n')
                        output['data'].write('{:10d}\n'.format(set_id))
                        start = False
                    if tmp_element_count > 7:
                        output['data'].write('\n')
                        tmp_element_count = 0
                    output['data'].write('{:10d}'.format(m + offset['element']))
                    tmp_element_count += 1
                if tmp_element_count <= 8:
                    output['data'].write('\n')
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
                for m in inp.set['node'][k]:
                    if start:
                        output['data'].write('*SET_NODE\n')
                        output['data'].write('{:10d}\n'.format(set_id))
                        start = False
                    if tmp_node_count > 7:
                        output['data'].write('\n')
                        tmp_node_count = 0
                    output['data'].write('{:10d}'.format(m + offset['node']))
                    tmp_node_count += 1
                if tmp_node_count <= 8:
                    output['data'].write('\n')
                count['nodeset'] += 1
                output['stats']['nsid'].append([set_id,set_name])

    update_term(True)
    k = ostream
    k.write(output['header'])
    k.write(output['timestamp'])
    k.write(output['sep'])
    # statistics
    k.write(comment_line('Model Stats'))
    k.write(set_comment_head)
    for i in output['stats']:
        for j in output['stats'][i]:
            k.write(set_comment_fmt.format(i,j[0],j[1]))
        k.write(set_comment_sep)
    output['data'].seek(0)
    k.write(output['sep'] + output['data'].read())
    output['data'].close()
    k.write(output['sep'])
    k.write('*END\n')
    k.write(comment_line('End of translated output.', fill='-', newline=False))
    return


def cmdline(argv = None):
    """ command line processor

    returns namespace via argparse, or throws SystemExit

    if argv is none, get from sys.argv (via argparse)

    """
    from . import _version
    version = _version.get_versions()['version']

    # argument parsing definitions

    parser = argparse.ArgumentParser(prog='abaqus2dyna',
                                     description='Translate Abaqus to LS-DYNA')
    parser.add_argument('--version',
                        action='version',
                        version='%(prog)s ' + version)
    parser.add_argument('input',
                        metavar='INPUT',
                        help='Abaqus keyword file')
    parser.add_argument('-o', '--output',
                        dest='output',
                        metavar='OUTPUT',
                        help='LS-DYNA keyword file output location')
    args = parser.parse_args(argv)

    return args


def convert(fin, fout):

    inp = ParseAbaqus(fin)
    #print(inp.count)

    # get nodes + elements (these will take the longest)
    total_nodel = 0
    for i in inp.instance:
        part = inp.part[inp.instance[i].part]
        total_nodel += len(part.node)
        total_nodel += len(part.element)

    # finally, output dyna keyword
    WriteDynaFromAbaqus(total_nodel, fin.name, inp, fout)

def main():
    args = cmdline()
    with open(args.input) as fin:
        if args.output:
            fout = open(args.output, 'w')
        else:
            fout = sys.stdout
        try:
            return convert(fin, fout)
        finally:
            if args.output:
                fout.close()

if __name__ == '__main__':
    sys.exit(main())

