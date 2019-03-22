# syscall-table

Generate JSON system call table from Linux source.

## Generating JSON
```
git clone https://github.com/HexRabbit/syscall-table && cd syscall-table
git clone https://github.com/torvalds/linux --depth=1
python gen_syscalls.py
```

## Web
* uses [jQuery DataTables](http://datatables.net/) to pull JSON file and format table
* links to https://elixir.bootlin.com for source cross-reference and http://www.kernel.org for manpages
* `www` dir checked into gh-pages branch w/ JSON file using `deploy.sh`

## Other
* tested on linux kernel v5.0.3
