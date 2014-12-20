__author__ = 'sunyanbin'

import os
import sys
import re
import getopt
import subprocess
import xml.etree.ElementTree as ET


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
    return line.startswith('res\\') and line.endswith('[UnusedResources]\n')


def get_file_name(line) -> str:
    return line[:line.index(':')]


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


def get_lint_log(log) -> list:
    if log:
        f = open(log)
        l = f.readlines()
        f.close()
        return l
    return os.popen("lint.bat --check UnusedResources .").readlines()


def remove_files(file_list):
    assert isinstance(file_list, list)
    for f in file_list:
        if os.path.exists(f):
            os.remove(f)


def remove_xml_nodes(xml, l):
    """
    remove node in 'l' AND all comments,
    this is a bug of ElementTree of Python.
    """
    if not os.path.exists(xml):
        return
    tree = ET.parse(xml)
    root = tree.getroot()
    for name in l:
        # get parent node
        p_node = root.find('.//*[@name="' + name + '"]/..')
        if p_node:
            # get the node to be removed
            node = p_node.find('./*[@name="' + name + '"]')
            p_node.remove(node)
            # print('remove xml node: ', node.text)
    tree.write(xml, encoding='UTF-8', xml_declaration=True)


def remove_xml_nodes_p(xml, l):
    if not os.path.exists(xml):
        return
    f = open(xml, 'r', encoding='utf-8')
    cstr = f.read()
    f.close()
    for name in l:
        _p = r"""
            .*\n                        # node之前的内容，我们不关心它
            (                           # 开始匹配node的内容
            \s*<\s*([a-zA-Z-]+)         # tag的开始部分，如' < string '，注意里面运行空白字符
            [^<>]*?                     # 其他可能存在的属性
            name\s*=\s*"                # name属性，如'name = "pref_camera_xxx"'
            """ + name + r"""           # name属性值
            "[^<>]*?>                   # tag开始部分的结束'>'符号，以及其他可能存在的属性
            .*?                         # node中除去tag之外的具体内容，ungreedy模式，否则会导致异乎寻常的大量匹配
            </\s*\2\s*>                 # tag的结束部分，\2引用了开始部分的tag内容
            [ \t]*\n*                   # tag结束之后可能还有空白，直到换行符的空格、制表符都删除掉
            )                           # 结束匹配node的内容
            .*                          # node之后的内容，我们同样不关心它
            """
        m = re.compile(_p, re.S | re.X).match(cstr)
        if m:
            node = m.group(1)
            node_index = cstr.find(node)
            cstr = str(cstr[:node_index] + cstr[node_index+len(node):])
            # print('remove xml node_pp: ', node)
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
            if get_node_type(line) not in supported_xml_node_type:
                print('unsuported xml node type: ', file_name)
                continue
            xml_dict = parsed_dict[xml_type]
            if file_name not in xml_dict:
                xml_dict[file_name] = []
            xml_dict[file_name].append(get_node_name(line))
        else:
            print('unknown file type: ', file_type, ' file name: ', file_name)
    return parsed_dict


def usage():
    print('\n' + sys.argv[0] + """

    Clean unused resources in Android App project.

    Usage:
        """ + sys.argv[0] + ' [options]' + """

    options:
        -h, --help: print help info.
        -v, --verbose: print verbose information when processing.
        -f <lint log file>
        --file <lint log file>
            use <lint log file>, otherwise call lint when processing.
    """)


def process(argv):
    verbose = False
    lint_log = None

    if argv:
        try:
            opts, args = getopt.getopt(argv, 'hf:v', ['help', 'file=', 'verbose'])
        except getopt.GetoptError:
            usage()
            sys.exit(1)
        for opt, arg in opts:
            if opt in ('-h', '--help'):
                usage()
                sys.exit()
            elif opt in ('-v', '--verbose'):
                verbose = True
            elif opt in ('-f', '--file'):
                lint_log = arg
            else:
                print('unknown options!')
                usage()

    print(">>>>>> start processing ...")
    print('>>>>>> get lint log, may need minutes...')
    content = get_lint_log(lint_log)
    if not content:
        print("""fatal error: cannot run lint on this project!
make sure 'lint' command is on your PATH dirs.""")
        return
    parsed_dict = parse(content)

    for k in parsed_dict.keys():
        if k == removable_file_type:
            print('\n>>>>>> remove unused files...')
            remove_files(parsed_dict[k])
            if verbose:
                print('\n'.join(parsed_dict[k]))
        elif k == xml_type:
            xml_info_dict = parsed_dict[k]
            for file_name in xml_info_dict.keys():
                print('\n>>>>>> remove unused xml nodes in ', file_name)
                remove_xml_nodes_p(file_name, xml_info_dict[file_name])
                if verbose:
                    print('\n'.join(xml_info_dict[file_name]))

if __name__ == '__main__':
    if len(sys.argv) > 1:
        process(sys.argv[1:])
    else:
        process(None)