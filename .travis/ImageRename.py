import os
import sys

# ATTENTION:  change these before start the script
OLD_VERSION_PREFIX = 'v1_'
NEW_VERSION_PREFIX = 'v1_'


def img_rename(path):
    if not path:
        return

    if not os.path.isdir(path):
        return

    folders = [path + '/' + f for f in os.listdir(path) if os.path.isdir(path + '/' + f)]
    for folder in folders:
        imgs = [x for x in os.listdir(folder)]
        if len(imgs) == 0:
            continue

        md_file = folder + '.md'
        processed_lines = []
        # key: old_img ; value: new_img
        img_map = {}
        with open(md_file, 'r', encoding='UTF-8') as r:
            for line in r.readlines():
                new_line = line
                for img in imgs:
                    if line.find('asset_img') > -1 and line.find(img) > -1:
                        new_img = get_new_img(img)
                        new_line = line.replace(img, new_img)
                        img_map[img] = new_img
                        continue

                processed_lines.append(new_line)

        with open(md_file, 'w', encoding='UTF-8') as r:
            r.writelines(processed_lines)
            r.flush()

        for img, new_img in img_map.items():
            os.rename(folder + '/' + img, folder + '/' + new_img)


def get_new_img(img: str):
    if img.find(OLD_VERSION_PREFIX) == 0:
        new_img = img.replace(OLD_VERSION_PREFIX, NEW_VERSION_PREFIX, 1)
    else:
        new_img = NEW_VERSION_PREFIX + img

    return new_img


if __name__ == '__main__':
    if OLD_VERSION_PREFIX == NEW_VERSION_PREFIX:
        print('error: old version must not be the same as new version')
        sys.exit(-1)

    img_rename(r'C:\workspace\ycwu314.github.io\source\_posts')
