"""NutRelay: Blackout Lab. Run with python3 app.py."""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import json, time
from engine import *
BG="#10151d"; PANEL="#192330"; FG="#eef4f7"; MUTED="#a1b1c2"; GREEN="#8ae7b0"; AMBER="#ffc56a"
PRESETS={"Festival":(2400,[120,75,230,95,400,65,180,50,200,125]),
         "Emergency supplies":(5000,[350,1200,550,240,700,85,125,450]),
         "Creator tips":(1000,[21,42,69,100,21,50,111,77,33,50])}
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("NutRelay | Blackout Lab"); self.geometry("1120x720"); self.minsize(880,650); self.configure(bg=BG)
        self.keyset=DEMO; self.result=None; self.pool=ThreadPoolExecutor(max_workers=1); self.busy=False
        self.protocol("WM_DELETE_WINDOW",self.close)
        style=ttk.Style(self); style.theme_use("clam")
        style.configure("TCombobox",fieldbackground=PANEL,background=PANEL,foreground=FG,arrowcolor=FG)
        style.configure("Treeview",background=PANEL,fieldbackground=PANEL,foreground=FG,rowheight=25,borderwidth=0)
        style.configure("Treeview.Heading",background="#253546",foreground=FG)
        style.map("Treeview",background=[("selected","#31506a")])
        top=tk.Frame(self,bg=BG); top.pack(fill="x",padx=24,pady=(18,10))
        tk.Label(top,text="NUTRELAY",font=("Sans",25,"bold"),fg=GREEN,bg=BG).pack(side="left")
        tk.Label(top,text="BLACKOUT LAB  /  CASHU OFFLINE READINESS",font=("Sans",11,"bold"),fg=MUTED,bg=BG).pack(side="left",padx=16)
        tk.Label(top,text="●  LOCAL ONLY",fg=GREEN,bg=BG,font=("Sans",10,"bold")).pack(side="right")
        body=tk.Frame(self,bg=BG);body.pack(fill="both",expand=True,padx=24,pady=(0,10))
        body.columnconfigure(0,weight=1,minsize=295);body.columnconfigure(1,weight=2,minsize=510);body.rowconfigure(0,weight=1)
        left=tk.Frame(body,bg=PANEL,padx=16,pady=14);left.grid(row=0,column=0,sticky="nsew",padx=(0,12))
        right=tk.Frame(body,bg=PANEL,padx=16,pady=14);right.grid(row=0,column=1,sticky="nsew")
        self.label(left,"01  /  PLAN YOUR BLACKOUT",GREEN,13,True)
        self.label(left,"Scenario",MUTED)
        self.preset=ttk.Combobox(left,values=list(PRESETS),state="readonly");self.preset.pack(fill="x",pady=(3,10));self.preset.set("Festival")
        self.preset.bind("<<ComboboxSelected>>",lambda _:self.load_preset())
        self.label(left,"Budget (sats)",MUTED)
        self.budget=tk.Entry(left,bg=BG,fg=FG,insertbackground=FG,relief="flat",font=("Sans",18));self.budget.pack(fill="x",ipady=6,pady=(3,10))
        self.label(left,"Forecast payments (one per line or comma)",MUTED)
        self.orders=tk.Text(left,height=5,bg=BG,fg=FG,insertbackground=FG,relief="flat",font=("Mono",11),wrap="word");self.orders.pack(fill="x",pady=(3,10))
        self.label(left,"02  /  PUBLIC MINT KEYSET",GREEN,13,True)
        self.keytext=tk.Label(left,text="",fg=MUTED,bg=PANEL,justify="left",wraplength=290);self.keytext.pack(anchor="w",pady=5)
        self.btn(left,"Import public /v1/keys JSON",self.import_keys)
        self.btn(left,"Reset to demo keyset",self.reset_key)
        self.runbutton=self.btn(left,"RUN BLACKOUT SIMULATION",self.run,accent=True)
        self.status=tk.Label(left,text="Ready. No real ecash is used.",fg=MUTED,bg=PANEL,justify="left",wraplength=290);self.status.pack(anchor="w",pady=8)
        self.label(right,"03  /  SURVIVAL DASHBOARD",GREEN,13,True)
        self.canvas=tk.Canvas(right,bg=PANEL,height=156,highlightthickness=0);self.canvas.pack(fill="x")
        self.canvas.bind("<Configure>",lambda _:self.draw())
        self.table=ttk.Treeview(right,columns=("denom","compact","ready"),show="headings",height=8)
        for k,title in [("denom","Denomination"),("compact","Compact proofs"),("ready","Prepared proofs")]:
            self.table.heading(k,text=title); self.table.column(k,width=110,anchor="center")
        self.table.pack(fill="both",expand=True,pady=(4,8))
        self.summary=tk.Label(right,text="Run a scenario to compare compact and prepared inventories.",bg=PANEL,fg=FG,justify="left",wraplength=490);self.summary.pack(anchor="w",pady=4)
        self.btn(right,"Export plan (JSON, no wallet secrets)",self.export)
        tk.Label(self,text="PLANNER ONLY  •  Offline receipt does not prevent double-spending. Mint trust, fees, expiry and recipient redemption still matter.",fg=MUTED,bg=BG,font=("Sans",9),wraplength=1000).pack(padx=16,pady=(0,8))
        self.load_preset();self.show_key();self.after(150,self.run)
    def label(self,p,text,color=FG,size=10,bold=False):
        tk.Label(p,text=text,bg=PANEL,fg=color,font=("Sans",size,"bold" if bold else "normal")).pack(anchor="w",pady=(4,2))
    def btn(self,p,text,cmd,accent=False):
        b=tk.Button(p,text=text,command=cmd,bg=GREEN if accent else "#273749",fg=BG if accent else FG,
            activebackground="#b9f5cf" if accent else "#405774",activeforeground=BG if accent else FG,
            relief="flat",font=("Sans",10,"bold"),pady=7,cursor="hand2");b.pack(fill="x",pady=3);return b
    def load_preset(self):
        b,o=PRESETS[self.preset.get()];self.budget.delete(0,"end");self.budget.insert(0,str(b));self.orders.delete("1.0","end");self.orders.insert("1.0",", ".join(map(str,o)))
    def show_key(self):
        k=self.keyset;self.keytext.config(text=("ID matches public data" if k.verified else "Synthetic demo keyset")+"\n"+str(len(k.denoms))+" supported denominations ≤100k • "+str(k.fee_ppk)+" ppk\n"+("Expires "+time.strftime("%Y-%m-%d UTC",time.gmtime(k.expiry)) if k.expiry else "No expiry provided"))
    def import_keys(self):
        path=filedialog.askopenfilename(filetypes=[("JSON files","*.json"),("All files","*")])
        if not path or self.busy:return
        try:
            with open(path,encoding="utf-8") as f: ks=read_keysets(f.read(1_000_001))
            if len(ks)>1: messagebox.showinfo("Multiple keysets","Using first eligible active sat keyset. Other keysets are ignored.")
            self.keyset=ks[0];self.show_key();self.clear_results()
        except Exception as e:messagebox.showerror("Invalid public keyset",str(e))
    def clear_results(self):
        self.result=None;self.draw()
        for x in self.table.get_children(): self.table.delete(x)
        self.summary.config(text="Run a new scenario with this keyset.")
    def reset_key(self):
        if self.busy:return
        self.keyset=DEMO;self.show_key();self.clear_results()
    def run(self):
        if self.busy:return
        try:
            b=int(self.budget.get());o=[int(x) for x in re.split(r"[,\s]+",self.orders.get("1.0","end").strip()) if x]
            validate(b,o);k=self.keyset
        except Exception as e: self.status.config(text=str(e),fg=AMBER);return
        self.busy=True;self.runbutton.config(state="disabled");self.status.config(text="Simulating outage scenarios…",fg=GREEN)
        future=self.pool.submit(compare,b,o,k)
        def poll():
            if not future.done():self.after(100,poll);return
            self.busy=False;self.runbutton.config(state="normal")
            try:
                self.result=future.result();self.context={"budget":b,"orders":o,"keyset_id":k.id,"fee_ppk":k.fee_ppk};self.render()
                self.status.config(text="Simulation complete. No money moved.",fg=GREEN)
            except Exception as e:self.status.config(text=str(e),fg=AMBER)
        self.after(100,poll)
    def draw(self):
        c=self.canvas;c.delete("all");w=max(c.winfo_width(),320)
        if not self.result:return
        r=self.result;n=len(r["prepared"]["steps"])
        vals=[("COMPACT / planned",100*r["baseline"]["success"]/n,AMBER),
              ("PREPARED / planned",100*r["prepared"]["success"]/n,GREEN),
              ("COMPACT / stress",r["stress"][0],AMBER),("PREPARED / stress",r["stress"][1],GREEN)]
        for i,(name,v,color) in enumerate(vals):
            y=8+i*37;c.create_text(0,y,anchor="nw",text=name,fill=MUTED,font=("Sans",9,"bold"))
            c.create_text(w-2,y,anchor="ne",text=f"{v:.1f}%",fill=color,font=("Sans",10,"bold"))
            c.create_rectangle(0,y+20,w,y+27,fill="#303d49",outline="")
            c.create_rectangle(0,y+20,w*v/100,y+27,fill=color,outline="")
    def render(self):
        r=self.result; self.draw()
        for x in self.table.get_children(): self.table.delete(x)
        for d in sorted(set(r["compact"])|set(r["ready"]),reverse=True):
            self.table.insert("","end",values=(f"{d:,} sats",r["compact"].get(d,0),r["ready"].get(d,0)))
        b,p=r["baseline"],r["prepared"]
        self.summary.config(text=f"Planned payments: {b['success']}/{len(b['steps'])} compact  →  {p['success']}/{len(p['steps'])} prepared\n"
          f"Proof count: {sum(r['compact'].values())} → {sum(r['ready'].values())}   |   {r['trials']} seeded stress scenarios\n"
          f"Prepared recipient redemption fee estimate: {p['recipient_fee_estimate']} sats (one swap per payment).\n"
          "Stress: pooled inventory, shuffled amounts ±20%; no mint contact.")
    def export(self):
        if not self.result:return messagebox.showinfo("No plan","Run a scenario first.")
        path=filedialog.asksaveasfilename(defaultextension=".json",initialfile="nutrelay-plan.json")
        if path: Path(path).write_text(json.dumps({"simulation_only":True,**self.context,**self.result},indent=2))
    def close(self):
        self.pool.shutdown(wait=False,cancel_futures=True);self.destroy()
if __name__=="__main__": App().mainloop()
