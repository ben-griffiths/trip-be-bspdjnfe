import json,urllib.request,datetime,sys
IDS={"Brussels":"d1CQLb7EukB9AEJJ2zPvIn0H7xsQ-Q","Ghent":"9mgx0fmk-H9ez3aZEFwWLMTW44rE7A","Bruges":"Spnc77B_tlBGbwuT-K84Oas7BYi5sg"}
out={}
for c,i in IDS.items():
    u="https://www.google.com/maps/preview/entitylist/getlist?authuser=0&hl=en&gl=uk&pb=!1m4!1s"+i+"!2e1!3m1!1e1!2e2!3e2!4i500!16b1"
    t=urllib.request.urlopen(urllib.request.Request(u,headers={"User-Agent":"Mozilla/5.0"}),timeout=30).read().decode("utf-8")
    t=t[t.index("\n")+1:] if t.startswith(")]}'") else t
    L=json.loads(t)[0]
    items=[]
    for it in (L[8] or []):
        p=it[1]
        items.append({"name":it[2],"note":it[3] or "","addr":p[4],"lat":p[5][2],"lng":p[5][3],"cid":str(int(p[6][1])%(1<<64))})
    out[c]=items
try:
    old=json.load(open("lists.json"))
    if old.get("lists")==out: print("unchanged"); sys.exit(0)
except Exception: pass
json.dump({"updated":datetime.datetime.utcnow().isoformat()+"Z","lists":out},open("lists.json","w"),ensure_ascii=False,indent=1)
print("updated")
