import re
import json
import sys
import platform
import os

META_INDICATOR = '---'
CODE_INDICATOR = '```'
HEADER_INDICATOR = '#'
LIST_INDICATOR = '-'

RE_CODE_IN_LINE = '`.*`'
RE_LINK_IN_LINE = '\[.*\]\(.+\)'
RE_MORE = '<!--[ ]+more[ ]+-->'
RE_IMG = '<img.+>'


def do_replace(path, secret_map_file):
    r = open(secret_map_file, 'r', encoding='UTF-8')
    cmap = json.load(r)
    r.close()

    code_block_flag = False
    meta_black_flag = False
    f = open(path, 'r', encoding='UTF-8')
    output_lines = []
    for line in f.readlines():
        if line.startswith(META_INDICATOR):
            meta_black_flag = not meta_black_flag
            output_lines.append(line)
            continue

        if meta_black_flag:
            output_lines.append(line)
            continue

        if line.startswith(CODE_INDICATOR):
            code_block_flag = not code_block_flag
            output_lines.append(line)
            continue

        if code_block_flag:
            output_lines.append(line)
            continue

        if line.startswith(HEADER_INDICATOR) or line.find('post_link') > 0 \
                or line.find('asset_img') > 0 or line.startswith('>') > 0 or line.startswith(LIST_INDICATOR) :
            output_lines.append(line)
            continue

        #   todo: 第二版再优化
        if re.search(RE_CODE_IN_LINE, line) or re.search(RE_LINK_IN_LINE, line) \
                or re.search(RE_MORE, line) or re.search(RE_IMG, line):
            output_lines.append(line)
            continue

        output_lines.append(do_replace_line(line, cmap))

    f.close()

    # 防止在本地覆盖文件
    if platform.system().find('Windows') > -1:
        for line in output_lines:
            print(line, end='')
    else:
        out = open(path, 'w', encoding='UTF-8')
        [out.writelines(line) for line in output_lines]
        out.flush()
        out.close()


def do_replace_line(line, cmap={}):
    #   &#x4F60;
    new_line = ''
    for ch in line:
        x = ch
        if ch in cmap:
            array = cmap[ch]
            x = '&#' + str(array[0]).replace('0x', 'x') + ';'
        new_line = new_line + x
    return new_line


# usage: folder mapping_file
if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("usage: <folder> <mapping_file>")
        exit(-1)

    folder = sys.argv[1]
    secret_map_file = sys.argv[2]
    filenames = [x for x in os.listdir(folder) if x.endswith('.md')]
    for fn in filenames:
        print('processing file:', fn)
        do_replace(folder + '/' + fn, secret_map_file)

# do_replace(r'C:\workspace\ycwu314.github.io\source\_posts\java-aqs.md', 'secret_map.json')
