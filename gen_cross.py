def select(i, wlist):
    return wlist[0]

filled = {}
while len(filled) != n_words:
    # find space with shortest word list
    _, i = min((len(l), i) for i, l in enumerate(wlists))
    # fill space with word from list
    if len(wlists[i]) == 0:
        sys.exit('Crossword unfilled!')
    filled[i] = w0 = select(i, wlists[i][:MIN_LOOK])
    # prune intersecting lists of conflicts
    new_wlists = {}
    for (x, j, y) in intersections[i]:
        new_wlists[j] = [w1 for w1 in wlists[j] if w0[x] == w1[y]]
    # backtrack if empty
    if min(len(l) for l in new_wlists) == 0:
        wlists[i].remove(filled[i])
        filled.pop(i, None)
        continue
    wlists.update(new_wlists)

print('Crossword filled!')
print(filled)
