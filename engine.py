import search
import chess
import chess.pgn
import sys
import traceback
import argparse

CACHE_SIZE = 200000
MINTIME = 0.1
TIMEDIV = 25.0
NODES = 800
C = 3.0


logfile = open("a0lite.log", "w")
LOG = True

def log(msg):
    if LOG:
        logfile.write(str(msg))
        logfile.write("\n")
        logfile.flush()

def send(str):
    log(">{}".format(str))
    sys.stdout.write(str)
    sys.stdout.write("\n")
    sys.stdout.flush()

def process_position(tokens):
    board = chess.Board()

    offset = 0

    if tokens[1] ==  'startpos':
        offset = 2
    elif tokens[1] == 'fen':
        fen = " ".join(tokens[2:8])
        board = chess.Board(fen=fen)
        offset = 8

    if offset >= len(tokens):
        return board

    if tokens[offset] == 'moves':
        for i in range(offset+1, len(tokens)):
            board.push_uci(tokens[i])

    # deal with cutechess bug where a drawn positions is passed in
    if board.can_claim_draw():
        board.clear_stack()
    return board





def load_network(net_name, device):
    log("Loading network ({} device={})".format(net_name, device))

    if net_name == "mg":
        inner = search.MeanGirlNet(device=device)
    elif net_name == "bg":
        inner = search.BadGyalNet(device=device)
    else:
        raise ValueError("unknown net: {}".format(net_name))
    return search.EPDLRUNet(inner, CACHE_SIZE)


def main():
    parser = argparse.ArgumentParser(description="A0 Lite")
    parser.add_argument("--net", choices=["mg", "bg"], default="mg",
                        help="network to use: mg=MeanGirl, bg=BadGyal (default: mg)")
    parser.add_argument("--runtime", choices=["cpu", "cuda", "mps"], default="cpu",
                        help="torch device: cpu, cuda, or mps (default: cpu)")
    args = parser.parse_args()

    send("A0 Lite")
    board = chess.Board()
    nn = None

    while True:
        line = sys.stdin.readline()
        line = line.rstrip()
        log("<{}".format(line))
        tokens = line.split()
        if len(tokens) == 0:
            continue

        if tokens[0] == "uci":
            send('id name A0 Lite')
            send('id author Dietrich Kappe')
            send('uciok')
        elif tokens[0] == "quit":
            exit(0)
        elif tokens[0] == "isready":
            if nn == None:
                nn = load_network(args.net, args.runtime)
            send("readyok")
        elif tokens[0] == "ucinewgame":
            board = chess.Board()

        elif tokens[0] == 'position':
            board = process_position(tokens)

        elif tokens[0] == 'go':
            my_nodes = NODES
            my_time = None
            if (len(tokens) == 3) and (tokens[1] == 'nodes'):
                my_nodes = int(tokens[2])
            if (len(tokens) == 3) and (tokens[1] == 'movetime'):
                my_time = int(tokens[2])/1000.0
                if my_time < MINTIME:
                    my_time = MINTIME
            if (len(tokens) == 9) and (tokens[1] == 'wtime'):
                wtime = int(tokens[2])
                btime = int(tokens[4])
                winc = int(tokens[6])
                binc = int(tokens[8])
                if (wtime > 5*winc):
                    wtime += 5*winc
                else:
                    wtime += winc
                if (btime > 5*binc):
                    btime += 5*binc
                else:
                    btime += binc
                if board.turn:
                    my_time = wtime/(TIMEDIV*1000.0)
                else:
                    my_time = btime/(TIMEDIV*1000.0)
                if my_time < MINTIME:
                    my_time = MINTIME
            if nn == None:
                nn = load_network(args.net, args.runtime)


            if my_time != None:
                best, score = search.UCT_search(board, 1000000, net=nn, C=C, max_time=my_time, send=send)
            else:
                best, score = search.UCT_search(board, my_nodes, net=nn, C=C, send=send)
            send("bestmove {}".format(best))

try:
    main()
except (SystemExit, KeyboardInterrupt):
    raise
except:
    exc_type, exc_value, exc_tb = sys.exc_info()
    log(traceback.format_exception(exc_type, exc_value, exc_tb))

logfile.close()
