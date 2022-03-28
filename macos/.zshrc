# This is where brew installs
export PATH="/usr/local/sbin:/usr/local/mysql/bin:$PATH"
PATH="$HOME/go/bin:$PATH"
HISTSIZE=9999999999
SAVEHIST=${HISTSIZE}
HISTFILESIZE=${HISTSIZE}

egrep '^PS1=' /etc/zshrc && echo 'Warning! Wrong prompt is set!'
