from ctags import CTags, TagEntry
from pathlib import Path
from lxml import html
from urllib.request import urlopen
from shutil import copyfileobj
from pathlib import Path
from tempfile import TemporaryDirectory
from halo import Halo
import requests
import tarfile
import subprocess
import ctags
import json
import sys
import re

def fetch_kernel(tmpdir):
    res = requests.get('https://www.kernel.org')
    tree = html.fromstring(res.text)
    linux_url = tree.xpath('//*[@id="releases"]/tr[1]/td[4]/a/@href')[0]
    filename = linux_url.split('/')[-1]
    tmpfile = Path(tmpdir.name) / filename

    with urlopen(linux_url) as fsrc, open(tmpfile, 'wb+') as fdst:
        copyfileobj(fsrc, fdst)

    with tarfile.open(tmpfile) as tar:
        linux_path = Path(tmpdir.name) / tar.next().name
        tar.extractall(tmpdir.name)

    return linux_path

def parse_line(linux, entry):
    file_name = entry['file'].decode()
    line_num = int(entry['lineNumber'])
    syscall_str = entry['pattern'][2:-2].decode()

    if syscall_str[-1] != ')':
        with open(linux / file_name, 'r') as f:
            start = False
            for i, line in enumerate(f):
                if i == line_num:
                    start = True
                if start:
                    line = line.strip()
                    syscall_str += line
                    if line[-1] == ')':
                        break

    match = re.search(r'SYSCALL_DEFINE(_COMPAT)?\d\((.*)\)', syscall_str)
    if not match:
        return None

    symbols = list(map(str.strip, match.group(2).split(',')[1:]))
    params = []
    for i in range(len(symbols)//2):
        params.append({
            'type': symbols[i*2] + ' ' + symbols[i*2+1],
            'def': None
        })

    return params + [{}]*(6-len(params))

def process_syscall(linux):
    syscall_func = []
    tags = CTags(str(linux / 'tags'))
    entry = TagEntry()
    syscall_tbl = open(linux / 'arch/x86/entry/syscalls/syscall_64.tbl', 'r')

    for line in syscall_tbl.readlines():
        line = line.strip()
        if line:
            if line.startswith('#'):
                continue
            else:
                syscall = re.search(r'(\d*)\s*(\w*)\s*(\w*)\s*(compat_)?(sys_)?(x32_)?(\w*)', line)
                if not syscall:
                    return None

                symbols = syscall.groups()
                func_id = int(symbols[0])
                func_type = symbols[1]
                func_name = symbols[2]
                func_fullname = symbols[6] if symbols[6] else 'not implemented'

                # fill the entry
                tags.find(entry, b'SYSCALL_DEFINE', ctags.TAG_PARTIALMATCH)

                while True:
                    filepath = entry['file']

                    # '[,\)]' is essential to filter mmap2 or the like
                    if re.search(r'SYSCALL_DEFINE(_COMPAT)?\d\('+func_fullname+r'[,\)]', entry['pattern'].decode()) \
                        and not (filepath.startswith(b'arch/') and not filepath.startswith(b'arch/x86')):

                        parsed = parse_line(linux, entry)
                        if not parsed:
                            return None

                        syscall_info = [
                            func_id,
                            func_name,
                            '{0:#04x}'.format(func_id)
                        ]
                        syscall_info += parsed
                        syscall_info += [entry['file'].decode(), entry['lineNumber']]
                        syscall_func.append(syscall_info)
                        break

                    elif not tags.findNext(entry):
                        syscall_func.append([
                            func_id,
                            func_name,
                            '{0:#04x}'.format(func_id),
                            {},
                            {},
                            {},
                            {},
                            {},
                            {},
                            '',
                            0
                        ])
                        break

    syscall_tbl.close()
    return syscall_func

def main():
    if len(sys.argv) < 2:
        print(f'Usage: {__file__} [path_to_linux | "FETCH"]')
        return

    if sys.argv[1] == 'FETCH':
        tmpdir = TemporaryDirectory()
        with Halo(text='Fetching Linux kernel', spinner='dots') as sp:
            try:
                linux = fetch_kernel(tmpdir)
            except Exception as e:
                sp.fail(e)
                return

            sp.succeed()
    else:
        linux = Path(sys.argv[1]).expanduser()

    valid_path = linux / 'kernel'
    if not valid_path.exists():
        print('Not a valid kernel path')
        return

    linux_version = subprocess.check_output('make kernelversion', cwd=linux, shell=True).decode().strip()
    if 'rc' in linux_version:
        matched = re.search(r'(\d*\.\d*)\.\d*-rc(\d*)', linux_version)
        if not matched:
            return

        linux_version = f'{matched.group(1)}-rc{matched.group(2)}'

    elif linux_version.endswith('.0'):
        linux_version = linux_version[:-2]

    tagfile = linux / 'tags'
    if not tagfile.exists():
        with Halo(text='Running ctags on kernel', spinner='dots') as sp:
            subprocess.run('ctags --fields=afmikKlnsStz --c-kinds=+pc -R', cwd=linux, shell=True)
            sp.succeed()

    with Halo(text='Processing syscalls', spinner='dots') as sp:
        syscall_func = process_syscall(linux)
        if not syscall_func:
            sp.fail()
            return

        sp.succeed()

    with open('www/syscall.json', 'w+') as f:
        f.write(
            json.dumps(
            {
                'aaData': syscall_func
            },
            sort_keys=True,
            indent=2
        ))

    with open('www/index.html.template', 'r') as f:
        html = f.read()
        html = html.replace('__LINUX_VERSION__', 'v' + linux_version)

    with open('www/index.html', 'w+') as f:
        f.write(html)

if __name__ == '__main__':
    main()
