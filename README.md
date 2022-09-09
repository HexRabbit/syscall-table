# syscall-table

Generate JSON system call table from Linux source.

## Usage

### Hosted on
https://syscall.hexrabbit.io

### Deploy
```
# install required packages
apt install ctags make

# clone repo
git clone https://github.com/HexRabbit/syscall-table
cd syscall-table

# install deps
poetry install

# automatically fetch the newest Linux source & generate static files
poetry run python3 gen_syscalls.py FETCH

# or use your specific Linux version
poetry run python3 gen_syscalls.py path/to/linux_source

# deploy to github pages
bash deploy.sh
```

## References
* Uses [jQuery DataTables](http://datatables.net/) to pull JSON file and format table
* Links to [Elixir Cross Referencer](https://elixir.bootlin.com) for source cross-reference and [The Linux Kernel Archives](http://www.kernel.org) for manpages
* Always synced with the latest Linux kernel by [Github Action](https://github.com/features/actions)
