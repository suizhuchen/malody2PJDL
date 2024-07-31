# malody2PJDL
# Author:Suichen
import string
import zipfile
import os
import json
import shutil
import random


def mcz_unzip(mcz_path: str) -> str:
    # 解决解压缩后乱码问题
    zip = zipfile.ZipFile(mcz_path, metadata_encoding='UTF-8')
    os.mkdir(mcz_path.split('.')[0])
    zip.extractall(mcz_path.split('.')[0])
    zip.close()
    return mcz_path.split('.')[0]


def gen_random_uid(length: int = 13) -> str:
    uid_random_str_list = list(string.ascii_lowercase) + list(string.digits)
    random_uid = ''
    for i in range(length):
        random_uid += uid_random_str_list[random.randint(0, len(uid_random_str_list) - 1)]
    return random_uid


def mc2json(mc_path: str, mc_dir: str) -> str:
    global sound_path, corrected
    if not mc_dir.endswith('\\'):
        mc_dir += '\\'
    print('mcz_path:', mc_dir)
    with open(f'{mc_path}', 'r', encoding='UTF-8') as mc:
        mc_json = json.load(mc)
    # 4k谱面检测
    if mc_json['meta']['mode_ext']['column'] != 4:
        return '非4k谱面，转换失败'
    # 非变速谱检测
    if len(mc_json['time']) != 1:
        return '谱面bpm非法（bpm信息错误/变速谱）'

    # 铺面信息提取 Part 1
    song_name = mc_json['meta']['song']['title']
    creator = mc_json['meta']['creator']
    info = f'曲师：{mc_json['meta']['song']['artist']}\n{mc_json['meta']['version']}'
    bg = mc_json['meta']['background']
    bpm = mc_json['time'][0]['bpm']

    os.makedirs(f'export/{song_name}', exist_ok=True)
    if not os.path.exists(f'export/{song_name}'):
        path_name = gen_random_uid()
    else:
        path_name = song_name
    if os.path.exists(f'export/{path_name}'):
        shutil.rmtree(f'export/{path_name}')
    if os.path.exists(f'export/{path_name}.pjdlc'):
        os.remove(f'export/{path_name}.pjdlc')
    os.makedirs(f'export/{path_name}')
    print('info:', [song_name, creator, info, bg, bpm])
    notes = list()
    # 主谱面提取
    for note in mc_json['note']:
        note = dict(note)
        if note.get('column', -1) != -1:
            # note种类判断
            if note.get('endbeat', None) is not None:
                # hold判定
                beat_i = round(int(note['beat'][1]) * 48) / int(note['beat'][2])
                drag = (int(note['endbeat'][0]) - int(note['beat'][0])) * 48 + (
                        round(int(note['endbeat'][1]) * 48) / int(note['endbeat'][2]) - beat_i)
                if drag <= 0:
                    return f'程序失误了，将下面这段信息保存\n\n\n{note}|{beat_i}|{drag}'
                single_note = [
                    note['beat'][0],
                    beat_i,
                    drag,
                    note['column']
                ]
            else:
                beat_i = round(int(note['beat'][1]) * 48) / int(note['beat'][2])
                single_note = [
                    note['beat'][0],
                    beat_i,
                    0,
                    note['column']
                ]
            notes.append(single_note)
        else:
            # TODO:fix offset
            corrected = int(note['offset']) / 1000
            sound_path = note['sound']
    # 导出

    shutil.copy(f'{mc_dir}{sound_path}', f'export/{path_name}/song.ogg')
    shutil.copy(f'{mc_dir}{bg}', f'export/{path_name}/cover.jpg')
    shutil.rmtree(mc_dir)

    # 构造json
    final_dict = dict()
    final_dict['author'] = creator
    final_dict['bpm'] = bpm
    final_dict['corrected'] = corrected
    final_dict['info'] = info
    final_dict['name'] = song_name
    final_dict['notes'] = notes
    final_dict['tags'] = []

    with open(f'export/{path_name}/chart.json', 'w', encoding='UTF-8') as chart:
        json.dump(final_dict, chart, ensure_ascii=False, indent=None)
    with open(f'export/{path_name}.pjdlc', 'wb+') as fo:
        with zipfile.ZipFile(file=fo, mode="w") as pjdlc:
            pjdlc.write(f'export/{path_name}/song.ogg', arcname='song.ogg')
            pjdlc.write(f'export/{path_name}/cover.jpg', arcname='cover.jpg')
            pjdlc.write(f'export/{path_name}/chart.json', arcname='chart.json')
    shutil.rmtree(f'export/{path_name}')
    return f'操作完成，请查看 export/{path_name}.pjdlc'


if __name__ == '__main__':
    mcz = input('请输入py文件目录下mcz名：')
    mcz_path = mcz.split('.')[0]
    if os.path.exists(mcz_path):
        shutil.rmtree(mcz_path)
    mcz_unzip(mcz)
    mc_files = list()
    for root, dirs, files in os.walk(mcz_path):
        for file in files:
            # 构建相对路径
            relative_path = os.path.relpath(os.path.join(root, file), mcz_path)
            if relative_path.endswith('.mc'):
                mc_files.append(relative_path)
    for i in range(len(mc_files)):
        print(f'{i}:{mc_files[i]}')

    nums = input('请输入欲转换mc文件名序号：')
    mc_dir = ''
    mc_path = os.path.relpath(os.path.join(mcz_path, mc_files[int(nums)]))
    for i in mc_path.split("\\")[:-1]:
        mc_dir += i + '\\'
    mc_dir = os.path.relpath(mc_dir)
    print(mc2json(mc_path, mc_dir))
