import io, re
t = io.open("main.tex", encoding="utf-8").read()
b = io.open("refs.bib", encoding="utf-8").read()
cited = set()
for m in re.finditer(r"\\cite\{([^}]*)\}", t):
    for k in m.group(1).split(","):
        cited.add(k.strip())
have = set(re.findall(r"@\w+\{([^,]+),", b))
print("引用 key 数", len(cited), " bib 条数", len(have))
print("缺 bib:", sorted(cited - have))
print("bib 未用:", sorted(have - cited))
