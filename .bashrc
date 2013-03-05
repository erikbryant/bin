# Source global definitions
if [ -f /etc/bashrc ]; then
	. /etc/bashrc
fi

# don't put duplicate lines in the history. See bash(1) for more options
export HISTCONTROL=ignoredups
# ... and ignore same sucessive entries.
export HISTCONTROL=ignoreboth
# ... and add timestamps
export HISTTIMEFORMAT="[%F %T] "

# check the window size after each command and, if necessary,
# update the values of LINES and COLUMNS.
shopt -s checkwinsize

PS1="\t(\$?)\W\$ "

PATH=$PATH:~/bin

if [ "$TERM" != "dumb" ]; then
    # The default color for directories is really hard to see. Change it.
    eval "`dircolors -b | sed s/di=01\;34/di=01\;31/1`"
    alias ls='ls --color=auto'
    alias vi=vim
fi
