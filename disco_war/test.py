import w3g


#f = w3g.File(r'C:\Users\User\Documents\Warcraft III\Replay\sv_bots.w3g')
f = w3g.File(r'C:\Users\User\Downloads\surv.w3g')

try:
    winner = f.player(f.winner())
except RuntimeError:
    print("No Winner")
else:
    print(winner.name)

f.print_apm()
