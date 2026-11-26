"""Interactive simulation replay. Only uses simulated payment results."""
import tkinter as tk
from tkinter import ttk
BG="#10151d"; PANEL="#192330"; FG="#eef4f7"; MUTED="#a1b1c2"; GREEN="#8ae7b0"; AMBER="#ffc56a"; RED="#ff8585"
class Replay(tk.Toplevel):
    def __init__(self, parent, result, context):
        super().__init__(parent)
        self.title("NutRelay | Blackout Replay"); self.geometry("850x610"); self.minsize(680,500)
        self.configure(bg=BG);self.result=result;self.context=context.copy();self.step=0;self.job=None;self.playing=False
        self.protocol("WM_DELETE_WINDOW",self.close)
        tk.Label(self,text="BLACKOUT / PAYMENT REPLAY",font=("Sans",20,"bold"),fg=GREEN,bg=BG).pack(anchor="w",padx=18,pady=(15,4))
        tk.Label(self,text="Mint connection unavailable (simulated)  •  No real payments",fg=MUTED,bg=BG).pack(anchor="w",padx=18)
        self.board=tk.Canvas(self,bg=PANEL,highlightthickness=0,height=230); self.board.pack(fill="x",padx=18,pady=12)
        self.board.bind("<Configure>",lambda e:self.draw())
        buttons=tk.Frame(self,bg=BG);buttons.pack(fill="x",padx=18)
        self.toggle=tk.Button(buttons,text="PLAY",command=self.play,bg=GREEN,fg=BG,font=("Sans",10,"bold"));self.toggle.pack(side="left",padx=(0,6))
        for label,cmd in [("NEXT PAYMENT",self.next),("RESTART",self.restart)]:
            tk.Button(buttons,text=label,command=cmd,bg=PANEL,fg=FG).pack(side="left",padx=6)
        self.progress=tk.Label(buttons,fg=MUTED,bg=BG);self.progress.pack(side="right")
        frame=tk.Frame(self,bg=PANEL);frame.pack(fill="both",expand=True,padx=18,pady=12)
        self.log=ttk.Treeview(frame,columns=("amount","compact","prepared"),show="headings",height=6)
        for k,title in [("amount","Payment (sats)"),("compact","Compact"),("prepared","Prepared")]:
            self.log.heading(k,text=title);self.log.column(k,anchor="center",width=140)
        sb=ttk.Scrollbar(frame,orient="vertical",command=self.log.yview);self.log.configure(yscrollcommand=sb.set);sb.pack(side="right",fill="y");self.log.pack(side="left",fill="both",expand=True)
        tk.Label(self,text="Prepared packets are preallocated. No offline double-spend prevention is implied.",fg=MUTED,bg=BG,wraplength=760).pack(pady=(0,10))
        self.draw()
    @property
    def total(self):return len(self.result["prepared"]["steps"])
    def draw(self):
        c=self.board;c.delete("all");w=max(c.winfo_width(),620);half=w/2
        c.create_line(half,12,half,215,fill="#344354")
        for i,(name,key,color) in enumerate([("COMPACT","baseline",AMBER),("PREPARED","prepared",GREEN)]):
            x=half*i+16; width=half-32
            steps=self.result[key]["steps"][:self.step]; paid=sum(s["amount"] for s in steps if s["success"]); n=sum(s["success"] for s in steps)
            remaining=self.context["budget"]-paid
            c.create_text(x,15,anchor="nw",text=name,fill=color,font=("Sans",13,"bold"))
            c.create_text(x,43,anchor="nw",text=f"{remaining:,} sats left",fill=FG,font=("Sans",23,"bold"))
            c.create_rectangle(x,86,x+width,98,fill="#303d49",outline="")
            c.create_rectangle(x,86,x+width*remaining/self.context["budget"],98,fill=color,outline="")
            c.create_text(x,112,anchor="nw",text=f"{n}/{self.step} completed",fill=MUTED,font=("Sans",12))
            if steps:
                s=steps[-1]; label="PAID" if s["success"] else "NO EXACT CHANGE"
                c.create_text(x,148,anchor="nw",text=f"{s['amount']:,} sats  /  {label}",fill=GREEN if s["success"] else RED,font=("Sans",11,"bold"))
                c.create_text(x,179,anchor="nw",text=f"Proofs used: {s['proofs']}  •  est. fee: {s['fee']} sats",fill=MUTED,font=("Sans",10))
            else:c.create_text(x,148,anchor="nw",text="Ready for the first payment",fill=MUTED)
        self.progress.config(text=f"PAYMENT {self.step} / {self.total}")
    def next(self):
        if self.step>=self.total:self.pause();return
        a,b=[self.result[k]["steps"][self.step] for k in ("baseline","prepared")]
        self.step+=1
        row=self.log.insert("","end",values=(f"{a['amount']:,}","PAID" if a["success"] else "FAILED","PAID" if b["success"] else "FAILED"));self.log.see(row);self.draw()
        if self.step==self.total:self.pause()
    def tick(self):
        self.job=None
        if not self.playing:return
        self.next()
        if self.playing:self.job=self.after(650,self.tick)
    def play(self):
        if self.playing:self.pause();return
        if self.step>=self.total:self.restart()
        self.playing=True;self.toggle.config(text="PAUSE");self.tick()
    def pause(self):
        self.playing=False
        if self.job is not None:self.after_cancel(self.job);self.job=None
        self.toggle.config(text="PLAY")
    def restart(self):
        self.pause();self.step=0
        for row in self.log.get_children():self.log.delete(row)
        self.draw()
    def close(self):self.pause();self.destroy()

class Inventory(tk.Toplevel):
    def __init__(self,parent,result):
        super().__init__(parent);self.title("NutRelay | Denomination Lab");self.geometry("790x590");self.configure(bg=BG)
        self.result=result;self.mode=tk.StringVar(value="count");self.selected=None
        tk.Label(self,text="DENOMINATION LAB",bg=BG,fg=GREEN,font=("Sans",20,"bold")).pack(anchor="w",padx=18,pady=(15,4))
        tk.Label(self,text="Select a denomination to compare its contribution to the two inventories.",bg=BG,fg=MUTED).pack(anchor="w",padx=18)
        controls=tk.Frame(self,bg=BG);controls.pack(fill="x",padx=18,pady=8)
        for title,v in [("Proof count","count"),("Face value (sats)","value")]:
            tk.Radiobutton(controls,text=title,variable=self.mode,value=v,command=self.draw,bg=BG,fg=FG,selectcolor=PANEL,activebackground=BG,activeforeground=FG).pack(side="left",padx=5)
        f=tk.Frame(self,bg=PANEL);f.pack(fill="both",expand=True,padx=18)
        self.canvas=tk.Canvas(f,bg=PANEL,highlightthickness=0);sb=ttk.Scrollbar(f,orient="vertical",command=self.canvas.yview);self.canvas.config(yscrollcommand=sb.set)
        sb.pack(side="right",fill="y");self.canvas.pack(side="left",fill="both",expand=True);self.canvas.bind("<Configure>",lambda e:self.draw())
        self.detail=tk.Label(self,bg=BG,fg=FG,justify="left",wraplength=720);self.detail.pack(anchor="w",padx=18,pady=12)
        self.draw()
    def draw(self):
        c=self.canvas;c.delete("all");w=max(c.winfo_width(),450);ds=sorted(set(self.result["compact"])|set(self.result["ready"]),reverse=True)
        multiplier=lambda d:d if self.mode.get()=="value" else 1
        peak=max([self.result[k].get(d,0)*multiplier(d) for k in ("compact","ready") for d in ds]+[1])
        c.create_text(12,12,anchor="nw",text="AMBER: compact     GREEN: prepared",fill=MUTED,font=("Sans",10,"bold"))
        for i,d in enumerate(ds):
            y=42+i*42;tag=f"d{d}"
            if self.selected==d:c.create_rectangle(2,y-3,w-2,y+38,fill="#273749",outline="",tags=tag)
            c.create_text(12,y+8,anchor="nw",text=f"{d:,}",fill=FG,tags=tag)
            for j,(k,col) in enumerate([("compact",AMBER),("ready",GREEN)]):
                n=self.result[k].get(d,0)*multiplier(d);yy=y+j*17
                c.create_rectangle(105,yy,105+(w-180)*n/peak,yy+12,fill=col,outline="",tags=tag)
                c.create_text(w-10,yy+6,anchor="e",text=f"{n:,}",fill=col,tags=tag)
            c.tag_bind(tag,"<Button-1>",lambda e,d=d:self.choose(d))
        c.configure(scrollregion=(0,0,w,50+len(ds)*42))
        if self.selected is None:self.detail.config(text="Click a denomination label or bar to inspect it.")
    def choose(self,d):
        self.selected=d;a=self.result["compact"].get(d,0);b=self.result["ready"].get(d,0)
        self.detail.config(text=f"{d:,} sats per proof  |  Compact: {a:,} proofs ({a*d:,} sats)  |  Prepared: {b:,} proofs ({b*d:,} sats)")
        self.draw()
