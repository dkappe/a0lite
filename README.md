# a0lite

*Is this lc0?* Definitely not. Lc0 is a clone of alpha zero chess, based on the paper by Deep Mind. Also, lc0 is a somewhat complicated, brittle bit of C++ code that runs into the thousand of lines. A0lite, by contrast, is a very simple python-based MCTS/UCT engine that tries to be simple and easy to understand.

The most basic NN MCTS engine in 95 lines of python. It's single threaded and doesn't make use of "smart" pruning or tree reuse. It's meant for tinkering. As such, more complex developments will be in branches rather than in the master. Also check out the forks and see what others are doing.

You will need to install [badgyal](https://github.com/dkappe/badgyal) for the neural nets.

By default it uses MeanGirl-8 (32x4) net on CPU. Plays about ~2050 CCRL in this configuration. The shell script `a0lite.sh` works as a uci engine. You can find a log file, `a0lite.log` in the same dir as the script.

Here is a sample cutechess-cli script for running a match:

```
#!/bin/bash

HOME=/home/dkappe
DIR=$PWD
A0=$HOME/deep3/src/a0lite/a0lite.sh
BAISLICKA=$HOME/chess/bin/baislicka
EGTB=$HOME/chess/egtb
CONCUR=1
BOOK=$HOME/chess/book/noomen3.pgn

cutechess-cli -concurrency $CONCUR \
              -tournament gauntlet -rounds 20 -games 2 -repeat \
              -engine name=A0Lite-CPU cmd=$A0 restart=on tc="0/1:0+1" proto=uci \
              -engine name=Baislicka cmd=$BAISLICKA tc="0/1:0+1" proto=uci \
              -openings file=$BOOK order=random format=pgn \
              -pgnout a0lite.pgn -recover \
              -tb $EGTB \
              -draw movenumber=100 movecount=5 score=10 \
              -resign movecount=5 score=900 \
              -each timemargin=2000
```
