import json,time,datetime,sys,subprocess,urllib.request,urllib.parse,re
IDS={"Brussels":"d1CQLb7EukB9AEJJ2zPvIn0H7xsQ-Q","Ghent":"9mgx0fmk-H9ez3aZEFwWLMTW44rE7A","Bruges":"Spnc77B_tlBGbwuT-K84Oas7BYi5sg"}
UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"
WUA="TripPageListSync/1.0 (https://github.com/ben-griffiths/trip-be-bspdjnfe)"
def get(u,ua=UA):
    h={"User-Agent":ua,"Accept-Language":"en-GB"}
    try:
        return urllib.request.urlopen(urllib.request.Request(u,headers=h),timeout=30).read().decode("utf-8")
    except Exception:
        return subprocess.run(["curl","-s","-m","30","-A",ua,"-H","Accept-Language: en-GB",u],capture_output=True).stdout.decode("utf-8")
def gjson(t):
    t=t.lstrip("\ufeff")
    if t.startswith(")]}'"): t=t[t.index("\n")+1:]
    return json.loads(t)
def find_place(x,hexid,name):
    st=[x]
    while st:
        y=st.pop()
        if isinstance(y,list):
            if len(y)>13 and isinstance(y[10],str) and ":" in y[10] and (y[10].split(":")[1].lower()==hexid or y[11]==name): return y
            st.extend(y)
    return None
def details(it):
    q=it["name"]+", "+it["addr"]
    u="https://www.google.com/search?tbm=map&authuser=0&hl=en&gl=gb&q="+urllib.parse.quote(q)
    p=find_place(gjson(get(u)),hex(int(it["cid"])),it["name"])
    if not p: return None
    d={"cats":p[13] or []}
    try: d["rating"]=p[4][7]; d["reviews"]=p[4][8]
    except Exception: pass
    try: d["price"]=p[4][2]
    except Exception: pass
    hrs={}
    try:
        for e in p[203][0]:
            y,m,dd=e[2]; key="%04d-%02d-%02d"%(y,m,dd); iv=[]
            for slot in (e[3] or []):
                lab=slot[0]
                if lab and lab.lower().startswith("closed"): continue
                if lab and "24 hours" in lab.lower(): iv.append([0,1440]); continue
                try:
                    o=slot[1][0]; c=slot[1][1]; om=o[0]*60+(o[1] if len(o)>1 else 0); cm=c[0]*60+(c[1] if len(c)>1 else 0)
                    if cm<=om: cm+=1440
                    iv.append([om,cm])
                except Exception: pass
            hrs[key]=iv
    except Exception: pass
    d["hours"]=hrs
    return d
STOP={"brugge","bruges","gent","ghent","bruxelles","brussels","restaurant","cafe","café","the","take","away","and","bar","brasserie","hotel","breakfast","lunch","with"}
def words(s): return {w for w in re.findall(r"[a-zà-ÿ']{4,}",s.lower()) if w not in STOP}
def image(it,sight):
    u="https://commons.wikimedia.org/w/api.php?"+urllib.parse.urlencode({"action":"query","generator":"geosearch","ggscoord":"%s|%s"%(it["lat"],it["lng"]),"ggsradius":"80","ggslimit":"20","ggsnamespace":"6","prop":"imageinfo","iiprop":"url","iiurlwidth":"320","format":"json"})
    try: pages=(json.loads(get(u,WUA)).get("query") or {}).get("pages") or {}
    except Exception: return None
    nw=words(it["name"]); sw=words(it["addr"].split(",")[0])
    best=None
    for pg in sorted(pages.values(),key=lambda p:p.get("index",99)):
        t=pg["title"].lower(); ii=(pg.get("imageinfo") or [{}])[0]; th=ii.get("thumburl")
        if not th or not re.search(r"\.(jpe?g|png)$",t): continue
        if nw and any(w in t for w in nw): return {"src":th,"kind":"photo","title":pg["title"][5:]}
        if sight and not best and any(w in t for w in sw|{"markt","rozenhoedkaai","bonifacius"}): best={"src":th,"kind":"photo","title":pg["title"][5:]}
    return best
SIGHT=("tourist attraction","bridge","historical","landmark","square","monument","museum","park","plaza","scenic","church")
try: old=json.load(open("lists.json",encoding="utf-8"))
except Exception: old={}
cache={}
for c,L in (old.get("lists") or {}).items():
    for it in L: cache[it.get("cid")]=it
out={}
for c,i in IDS.items():
    u="https://www.google.com/maps/preview/entitylist/getlist?authuser=0&hl=en&gl=uk&pb=!1m4!1s"+i+"!2e1!3m1!1e1!2e2!3e2!4i500!16b1"
    L=gjson(get(u))[0]
    items=[]
    for it in (L[8] or []):
        p=it[1]
        items.append({"name":it[2],"note":it[3] or "","addr":p[4],"lat":p[5][2],"lng":p[5][3],"cid":str(int(p[6][1])%(1<<64))})
    out[c]=items
now=time.time()
for c,items in out.items():
    for it in items:
        old_it=cache.get(it["cid"]) or {}
        fresh=old_it.get("det_at",0)>now-6*3600 and old_it.get("det")
        if fresh: it["det"]=old_it["det"]; it["det_at"]=old_it["det_at"]
        else:
            try: d=details(it)
            except Exception as e: d=None; print("details failed",it["name"],e)
            if d: it["det"]=d; it["det_at"]=now
            elif old_it.get("det"): it["det"]=old_it["det"]; it["det_at"]=old_it.get("det_at",0)
            time.sleep(1.5)
        if "img" in old_it: it["img"]=old_it["img"]
        else:
            cats=" ".join((it.get("det") or {}).get("cats") or []).lower()
            try: it["img"]=image(it,any(s in cats for s in SIGHT))
            except Exception as e: it["img"]=None
            time.sleep(1.0)
strip=lambda L:{c:[{k:v for k,v in it.items() if k!="det_at"} for it in v] for c,v in L.items()}
if old.get("lists") and strip(old["lists"])==strip(out):
    print("unchanged"); sys.exit(0)
json.dump({"updated":datetime.datetime.utcnow().isoformat()+"Z","lists":out},open("lists.json","w",encoding="utf-8"),ensure_ascii=False,indent=1)
print("updated", {c:len(v) for c,v in out.items()}, "with details:", sum(1 for v in out.values() for it in v if it.get("det")), "photos:", sum(1 for v in out.values() for it in v if it.get("img")))
