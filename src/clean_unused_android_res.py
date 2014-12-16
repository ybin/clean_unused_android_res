__author__ = 'sunyanbin'

import os
import re

xml_type = 'xml'
removable_file_type = "removable"
supported_xml_node_type = ('color', 'dimen', 'string', 'array', 'string-array')

node_name_p = re.compile(r'.*R\.\S+\.(\S+).*')
node_type_p = re.compile(r'.*R\.(\S+)\.\S+.*')
drawable_xml_p = re.compile(r'.*res\\drawable\\\S+\.xml.*')
anim_xml_p = re.compile(r'.*res\\anim\\\S+\.xml')
layout_xml_p = re.compile(r'.*res\\layout\\\S+\.xml.*')
menu_xml_p = re.compile(r'.*res\\menu\\\S+\.xml.*')
raw_file_p = re.compile(r'.*res\\raw\\.*')

def is_valid_line(line):
    return line.endswith('[UnusedResources]\n')

def get_file_name(line) -> str:
    file_name = ''
    if is_valid_line(line):
        file_name = line[:line.index(':')]
    return file_name

def get_line_num(line) -> str:
    line_num = ''
    if is_valid_line(line):
        start = line.index(':') + 1
        line_num = line[start:line.index(':', start)]
        if not line_num.isdigit():
            line_num = ''
    return line_num

def get_node_type(line) -> str:
    ret = ''
    m = node_type_p.match(line)
    if m:
        ret = m.group(1)
    return ret

def get_node_name(line) -> str:
    ret = ''
    m = node_name_p.match(line)
    if m:
        ret = m.group(1)
    return str(ret)

def get_file_type(_path) -> str:
    _type = ''
    if drawable_xml_p.match(_path) or menu_xml_p.match(_path) or \
            raw_file_p.match(_path) or anim_xml_p.match(_path) or \
            layout_xml_p.match(_path) or _path.endswith('.png'):
        _type = removable_file_type
    elif _path.endswith('.xml'):
        _type = xml_type
    return _type



def get_lint_log(test) -> list:
    assert isinstance(test, bool)
    if test:
        f = open("lint.log")
        l = f.readlines()
        f.close()
        return l

    return os.popen("lint --check UnusedResources .").readlines()

def remove_files(file_list):
    assert isinstance(file_list, list)
    for f in file_list:
        if os.path.exists(f):
            os.remove(f)
            print("delete img file: ", f)

def remove_xml_nodes(xml, l):
    if not os.path.exists(xml):
        return

    f = open(xml, 'r', encoding='utf-8')
    cstr = f.read()
    f.close()
    for name in l:
        tmp_index = cstr.find('name="'+name+'"')
        if tmp_index == -1:
            continue
        start_index = cstr.rfind('<', tmp_index-20, tmp_index)+1
        tag = cstr[start_index:cstr.find(' ', start_index)]
        end_index = cstr.index('</'+tag+'>', start_index) + len('</'+tag+'>') + 1
        cstr = str(cstr[:start_index-1] + cstr[end_index:])
        print('remove xml node: ', name, ' in ', xml)
    f = open(xml, 'w', encoding='utf-8')
    f.write(cstr)
    f.close()
    
def get_node(name, cstr) -> str:
    tag_pstr = r'.*<\s*([a-z\-A-Z]+)\s+name="' + name + r'".*'
    tag_p = re.compile(tag_pstr, re.S)
    tag_m = tag_p.match(cstr)
    if tag_m:
        tag = tag_m.group(1)
        start_tag = r'.*\n(\s*<\s*' + tag + r'\s+name\s*=\s*"' + name + r'"[^>]*>'
        end_tag = r'</\s*' + tag + r'\s*>[ \t]*\n*).*'
        node_pstr = start_tag + r'.*?' + end_tag
        node_p = re.compile(node_pstr, re.S)
        node_m = node_p.match(cstr)
        if node_m:
            return node_m.group(1)
    return None
    
def remove_xml_nodes_p(xml, l):
    if not os.path.exists(xml):
        return

    f = open(xml, 'r', encoding='utf-8')
    cstr = f.read()
    f.close()
    for name in l:
        node = get_node(name, cstr)
        if node:
            node_index = cstr.find(node)
            cstr = str(cstr[:node_index] + cstr[node_index+len(node):])
            #print('remove xml node: ', node)
    f = open(xml, 'w', encoding='utf-8')
    f.write(cstr)
    f.close()

def parse(content):
    """
    parse lint log file.

    parse() will return a internal used dictionary
    with this format:
    {
        'png' : [ file name list ],
        'ogg' : [ file name list ],
        'xml' : # another dictionary
        {
            'res/values/strings.xml' : [ node name list ]
            'res/values/arrays.xml'  : [ node name list ]
            # ......
        }
        # other file types
    }

    :param content: content of lint log file, a list
    :return: the dictionary
    """

    parsed_dict = {
        removable_file_type: [],
        xml_type: {},
    }
    for line in content:
        if not is_valid_line(line):
            continue

        file_name = get_file_name(line)
        file_type = get_file_type(file_name)

        if file_type == removable_file_type:
            parsed_dict[file_type].append(file_name)
        elif file_type == xml_type:
            if not get_node_type(line) in supported_xml_node_type:
                print('unsuported xml node type: ', file_name)
                continue
            xml_dict = parsed_dict[xml_type]
            if not file_name in xml_dict:
                xml_dict[file_name] = []
            xml_dict[file_name].append(get_node_name(line))
        else:
            print('unknown file type: ', file_type, ' file name: ', file_name)

    return parsed_dict

def dump_dict(d):
    for k in d.keys():
        if k == removable_file_type:
            print('\n>>>>>> remove unused files...')
            print('\n'.join(d[k]))
            print()
        elif k == xml_type:
            xml_info_dict = d[k]
            for file_name in xml_info_dict.keys():
                print('\n>>>>>> remove unused xml nodes in ', file_name)
                print('\n'.join(xml_info_dict[file_name]))
                print()

def main():
    print(">>>>>> start processing ...")

    print('>>>>>> get lint log...')
    parsed_dict = parse(get_lint_log(True))

    if False:
        dump_dict(parsed_dict)
        return

    for k in parsed_dict.keys():
        if k == removable_file_type:
            print('\n>>>>>> remove unused files...')
            remove_files(parsed_dict[k])
        elif k == xml_type:
            xml_info_dict = parsed_dict[k]
            for file_name in xml_info_dict.keys():
                print('\n>>>>>> remove unused xml nodes in ', file_name)
                remove_xml_nodes_p(file_name, xml_info_dict[file_name])

if __name__ == '__main__':
    main()
