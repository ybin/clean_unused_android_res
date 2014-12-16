__author__ = 'sunyanbin10130990'

import os
import re
import xml.etree.ElementTree as ET

xml_type = 'xml'
layout_type = 'layout'
removable_file_type = "removable"

name_attr_p = re.compile(r'.*R\.\S+\.(\S+).*')
drawable_xml_p = re.compile(r'.*res\\drawable\\\S+\.xml.*')
anim_xml_p = re.compile(r'.*res\\anim\\\S+\.xml')
layout_p = re.compile(r'.*res\\layout\\\S+\.xml.*')
raw_p = re.compile(r'.*res\\raw\\.*')

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

def get_file_type(_path) -> str:
    _type = ''
    if drawable_xml_p.match(_path) or raw_p.match(_path) or anim_xml_p.match(_path) or _path.endswith('.png'):
        _type = removable_file_type
    elif _path.endswith('.xml') and not layout_p.match(_path):
        _type = xml_type
    elif layout_p.match(_path):
        _type = layout_type
    return _type

def get_node_name(line) -> str:
    """
    get 'name' attribute of xml node.

    :param line: line of lint log
    :return: value of 'name' attribute
    """
    ret = ''
    m = name_attr_p.match(line)
    if m:
        ret = m.group(1)
    return str(ret)


def get_lint_log(test) -> list:
    assert isinstance(test, bool)
    if test:
        f = open("lint.log")
        l = f.readlines()
        f.close()
        return l

    return os.popen("lint --check UnusedResources .").readlines()

def remove_files(file_list):
    """
    remove files.

    :param file_list: a list of files
    :return: None
    """
    assert isinstance(file_list, list)
    for f in file_list:
        if os.path.exists(f):
            os.remove(f)
            print("delete img file: ", f)

def remove_xml_nodes(xml, name_list):
    """
    remove xml nodes.

    :param xml: xml file name
    :param name_list: 'name' list of nodes in 'xml'
    :return: None
    """
    if not os.path.exists(xml):
        return

    tree = ET.parse(xml)
    root = tree.getroot()
    for name in name_list:
        x = ".//*[@name='"+name+"']"
        node = root.find(x)
        if node == None:
            print('remove node failed: ', name)
        else:
            root.remove(node)
            print('remove node: ', name)
    tree.write(xml)

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
            xml_dict = parsed_dict[xml_type]
            if file_name in xml_dict:
                xml_dict[file_name].append(get_node_name(line))
            else:
                xml_dict[file_name] = [get_node_name(line)]
        else:
            print('unknown file type: ', file_type, ' file name: ', file_name)

    return parsed_dict

def dump_dict(d):
    for k in d.keys():
        if k == removable_file_type:
            print('>>>>>> remove unused files...')
            print('\n'.join(d[k]))
            print()
        elif k == xml_type:
            xml_info_dict = d[k]
            for file_name in xml_info_dict.keys():
                print('>>>>>> remove unused xml nodes in ', file_name)
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
            print('>>>>>> remove unused files...')
            #remove_files(parsed_dict[k])
        elif k == xml_type:
            xml_info_dict = parsed_dict[k]
            for file_name in xml_info_dict.keys():
                print('>>>>>> remove unused xml nodes in ', file_name)
                remove_xml_nodes(file_name, xml_info_dict[file_name])

if __name__ == '__main__':
    main()
