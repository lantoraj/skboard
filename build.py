"""Builds public/index.html from the source files in data/: python3 build.py"""
import glob, json, math, re
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).parent
DATA = ROOT / "data"
KR = ["Bratislavský", "Trnavský", "Trenčiansky", "Nitriansky", "Žilinský", "Banskobystrický", "Prešovský", "Košický"]
SR = "Slovenská republika"

# id, name, ambulance specialties (NCZI CISR_ODB_POPIS), hospital programs (MZ SR name, column label)
G=[
 ("gastro","Gastroenterológia a hepatológia",["gastroenterológia","hepatológia","pediatrická gastroenterológia, hepatológia a výživa"],
  [("Program gastroenterológie a hepatológie","Gastro a hepat."),("Program brušnej chirurgie","Brušná chir."),("Onkochirurgický program","Onkochir."),("Program pediatrickej gastroenterológie, hepatológie a porúch výživy","Ped. gastro")]),
 ("kardio","Kardiológia a angiológia",["kardiológia","pediatrická kardiológia","angiológia"],
  [("Neinvazívny kardiovaskulárny program","Neinvaz. kardio"),("Program intervenčnej kardiológie","Interv. kardio"),("Program intervenčnej arytmológie","Arytmológia"),("Kardiochirurgický program","Kardiochir."),("Program cievnej chirurgie","Cievna chir."),("Program pediatrickej kardiológie","Ped. kardio")]),
 ("onko","Onkológia",["klinická onkológia","radiačná onkológia","onkológia v gynekológii","onkológia v chirurgii","onkológia v urológii","pediatrická hematológia a onkológia"],
  [("Program klinickej onkológie","Klin. onko"),("Program radiačnej onkológie","Radiačná onko"),("Onkochirurgický program","Onkochir."),("Program pediatrickej hematológie a onkológie","Ped. hemato-onko")]),
 ("chir","Chirurgia",["chirurgia","úrazová chirurgia","cievna chirurgia","plastická chirurgia","detská chirurgia"],
  [("Program brušnej chirurgie","Brušná chir."),("Traumatologický program","Traumatológia"),("Program cievnej chirurgie","Cievna chir."),("Program chirurgie kože, podkožia a prsníka","Koža a prsník"),("Program plastickej chirurgie","Plastická"),("Program detskej chirurgie","Detská chir.")]),
 ("orto","Ortopédia",["ortopédia","pediatrická ortopédia"],
  [("Ortopedický program","Ortopedický"),("Spondylochirurgický program","Spondylochir."),("Traumatologický program","Traumatológia"),("Ortopedický program pre deti","Ortop. deti")]),
 ("neuro","Neurológia a neurochirurgia",["neurológia","pediatrická neurológia","neurochirurgia"],
  [("Neurologický program","Neurologický"),("Neurochirurgický program","Neurochir."),("Program intervenčnej neurorádiológie","Interv. neurorad."),("Program pediatrickej neurológie","Ped. neuro")]),
 ("uro","Urológia",["urológia","pediatrická urológia"],[("Urologický program","Urologický"),("Urologický program pre deti","Urológia deti")]),
 ("gyn","Gynekológia a pôrodníctvo",["gynekológia a pôrodníctvo","reprodukčná medicína","pediatrická gynekológia"],
  [("Gynekologický program","Gynekologický"),("Pôrodnícky program","Pôrodnícky"),("Gynekologický program pre deti","Gyn. deti")]),
 ("oftal","Oftalmológia",["oftalmológia","pediatrická oftalmológia"],[("Oftalmologický program","Oftalmologický"),("Program detskej oftalmológie","Oftal. deti")]),
 ("orl","Otorinolaryngológia",["otorinolaryngológia","pediatrická otorinolaryngológia","foniatria"],[("Otorinolaryngologický program","ORL"),("Otorinolaryngologický program pre deti","ORL deti")]),
 ("diab","Diabetológia a endokrinológia",["diabetológia, poruchy látkovej premeny a výživy","endokrinológia","pediatrická endokrinológia a diabetológia, poruchy látkovej premeny a výživy"],
  [("Program endokrinológie, diabetológie a metabolických porúch","Endo a diabeto"),("Program pediatrickej endokrinológie, diabetológie a vrodených chýb metabolizmu","Ped. endo")]),
 ("pneumo","Pneumológia",["pneumológia a ftizeológia","pediatrická pneumológia a ftizeológia"],
  [("Program pneumológie a ftizeológie","Pneumológia"),("Program hrudníkovej chirurgie","Hrudníková chir."),("Program pediatrickej pneumológie a ftizeológie","Ped. pneumo")]),
 ("nefro","Nefrológia",["nefrológia","pediatrická nefrológia"],
  [("Nefrologický program","Nefrologický"),("Program pre orgánové transplantácie","Transplantácie"),("Program pediatrickej nefrológie","Ped. nefro")]),
 ("derma","Dermatovenerológia",["dermatovenerológia","detská dermatovenerológia"],[("Dermatovenerologický program","Dermato"),("Dermatovenerologický program pre deti","Dermato deti")]),
 ("psych","Psychiatria",["psychiatria","detská psychiatria","gerontopsychiatria","medicína drogových závislostí"],[("Psychiatrický program","Psychiatrický"),("Program pediatrickej psychiatrie","Ped. psychiatria")]),
 ("reuma","Reumatológia",["reumatológia","pediatrická reumatológia"],[("Reumatologický program","Reumatologický"),("Program pediatrickej reumatológie","Ped. reuma")]),
 ("imuno","Imunológia a alergológia",["klinická imunológia a alergológia","pediatrická imunológia a alergiológia"],
  [("Program klinickej imunológie a alergológie","Imuno a alergo"),("Program pediatrickej imunológie a alergológie","Ped. imuno")]),
 ("hema","Hematológia",["hematológia a transfuziológia"],[("Program hematológie a transfuziológie","Hematológia"),("Program pediatrickej hematológie a onkológie","Ped. hemato-onko")]),
 ("intern","Vnútorné lekárstvo a geriatria",["vnútorné lekárstvo","geriatria"],[("Program internej medicíny","Interná medicína"),("Program paliatívnej medicíny","Paliatívna")]),
]

# ICD-10 chapter used for hospitalizations of each group; ALL = all chapters
CHAPTER = {"gastro": "XI", "kardio": "IX", "onko": "II", "chir": "XIX", "orto": "XIII", "neuro": "VI", "uro": "XIV", "gyn": "XV",
           "oftal": "VII", "orl": "VIII", "diab": "IV", "pneumo": "X", "nefro": "XIV", "derma": "XII", "psych": "V", "reuma": "XIII",
           "imuno": "III", "hema": "III", "intern": "ALL"}
ROMAN = {"I.": 1, "II.": 2, "III.": 3, "IV.": 4, "V.": 5}


def num(v):
    return None if str(v).strip() in ("–", "-", "x", "nan", "") else float(v)


def shapes():
    geo = json.loads((DATA / "kraje_natural_earth.geojson").read_text())
    rename = {"Prešov": "Prešovský", "Trenciansky": "Trenčiansky"}
    lon0, lat0, kx, scale = 16.8, 49.65, math.cos(math.radians(48.7)), 190
    out = {}
    for f in geo["features"]:
        name = rename.get(f["properties"]["name"], f["properties"]["name"])
        g = f["geometry"]
        rings = g["coordinates"] if g["type"] == "Polygon" else [r for poly in g["coordinates"] for r in poly]
        pts = [((lo - lon0) * kx * scale, (lat0 - la) * scale) for lo, la in max(rings, key=len)]
        a = cx = cy = 0
        for (x1, y1), (x2, y2) in zip(pts, pts[1:] + pts[:1]):
            cr = x1 * y2 - x2 * y1
            a += cr; cx += (x1 + x2) * cr; cy += (y1 + y2) * cr
        out[name] = {"d": "M" + "L".join(f"{x:.1f},{y:.1f}" for x, y in pts) + "Z",
                     "cx": round(cx / (3 * a), 1), "cy": round(cy / (3 * a), 1)}
    return out


def network():
    d = pd.concat(pd.read_excel(f, sheet_name="Dataset") for f in sorted(glob.glob(str(DATA / "nczi_siet" / "*_T2.xlsx"))))
    d["ROK_SPRAC"] = d["ROK_SPRAC"].astype(int)
    for c in ["UTV_POC", "NAVSTEVY_UTV", "PR_PP_MPP_UV_A01", "PR_PP_MPP_UV_D01", "PR_PP_MPP_UV_E01"]:
        d[c] = pd.to_numeric(d[c], errors="coerce").fillna(0)
    d["kraj"] = d["UZEMIE_POPIS"].str.replace(" kraj", "", regex=False)
    d["odb"] = d["CISR_ODB_POPIS"].astype(str).str.strip()
    code = d["DRUH_ZZ"].astype(str).str[:4]
    d["typ"] = code.map(lambda c: "nem" if c.startswith("02") else "pol" if c == "0106" else "amb" if c == "0102" else "ine")
    amb = d[d.UTVAR_VYSTUP == "ambulancia_výstup"]
    jzs = d[d.UTVAR_VYSTUP == "útvar jednodňovej zdravotnej starostlivosti"]
    stats = {}
    for gid, _, specs, _ in G:
        a, j, out = amb[amb.odb.isin(specs)], jzs[jzs.odb.isin(specs)], {}
        for (y, k), s in a.groupby(["ROK_SPRAC", "kraj"]):
            t = s.groupby("typ")["UTV_POC"].sum()
            out.setdefault(k, {})[str(y)] = [
                int(s.UTV_POC.sum()), int(s.NAVSTEVY_UTV.sum()), round(float(s.PR_PP_MPP_UV_A01.sum()), 1),
                round(float(s.PR_PP_MPP_UV_D01.sum() + s.PR_PP_MPP_UV_E01.sum()), 1),
                int(j[(j.ROK_SPRAC == y) & (j.kraj == k)].UTV_POC.sum()),
                int(t.get("nem", 0)), int(t.get("pol", 0)), int(t.get("amb", 0)), int(t.get("ine", 0))]
        stats[gid] = out
    return stats, [str(y) for y in sorted(d.ROK_SPRAC.unique())]


def hospitals():
    xl = DATA / "Zoznam_kategorizovanych_nemocnic_2026_programy.xlsx"
    names = sorted({p for g in G for p, _ in g[3]})
    idx = {p: i for i, p in enumerate(names)}
    levels = {}
    for sheet in ["Povinné programy", "Doplnkové programy"]:
        p = pd.read_excel(xl, sheet_name=sheet, header=1)
        p["nm"] = p["Názov programu"].astype(str).str.strip()
        for _, r in p[p.nm.isin(idx)].iterrows():
            h = levels.setdefault(r["Kód nemocnice"], {})
            i = idx[r.nm]
            h[i] = max(h.get(i, 0), ROMAN.get(str(r["Úroveň programu"]).strip(), 0))
    hl = pd.read_excel(xl, sheet_name="Zoznam nemocníc", header=2).dropna(subset=["Kód PZS"])
    hosp = [{"k": str(r["Kraj"]).strip(), "c": r["Kód PZS"], "l": str(r["Úroveň"]).strip(),
             "n": " ".join(str(r["Názov nemocnice"]).split()), "t": str(r["Typ nemocnice"]).replace(" nemocnica", ""),
             "p": levels.get(r["Kód PZS"], {})} for _, r in hl.iterrows()]
    groups = [{"id": g[0], "name": g[1], "specs": g[2], "ch": CHAPTER[g[0]],
               "progs": [[idx[p], label, p] for p, label in g[3]]} for g in G]
    return hosp, groups


def chapter_key(s):
    s = str(s).strip()
    if s.startswith("Spolu"):
        return "ALL"
    m = re.match(r"^([IVXL]+)\.", s)
    return m.group(1) if m else None


def hospitalizations():
    hs, pop, flows, chn, dg = {}, {}, {}, {}, {}
    files = sorted(glob.glob(str(DATA / "nczi_hospitalizacie" / "*.xlsx")))
    for f in files:
        y = re.search(r"(\d{4})\.xlsx", f).group(1)
        x = pd.ExcelFile(f)
        # sheet names vary between years ("P3 ", "T4_(aktualizovany_grafG3)")
        sheet = lambda n: next(s for s in x.sheet_names if s.strip() == n or (n == "T4" and s.startswith("T4_(")))
        for i, k in enumerate([SR] + KR):
            t = pd.read_excel(x, sheet_name=sheet("T4") if k == SR else sheet(f"T4_{i}"), header=None)
            h4, h5 = [str(v) for v in t.iloc[4]], [str(v) for v in t.iloc[5]]
            col = lambda row, pat: next(j for j, v in enumerate(row) if pat in v)
            cp, ca, cl, cd = col(h5, "na 100 000"), col(h4, "Priemerný vek"), col(h4, "Priemerný ošetrova"), col(h5, "na 1 000 hosp")
            for r in t.itertuples(index=False):
                c = chapter_key(r[0])
                if not c:
                    continue
                if c != "ALL":
                    chn[c] = re.sub(r"\s+", " ", str(r[0])).strip()
                hs.setdefault(c, {}).setdefault(k, {})[y] = [num(r[1]), num(r[cp]), num(r[ca]), num(r[cl]), num(r[cd])]
        for r in pd.read_excel(x, sheet_name=sheet("P3"), header=None).itertuples(index=False):
            n = str(r[10]).strip().replace(" kraj", "")
            if (n in KR or n == SR) and n not in pop.get(y, {}):
                pop.setdefault(y, {})[n] = float(r[11])
        flows[y] = {}
        for r in pd.read_excel(x, sheet_name=sheet("T17"), header=None).itertuples(index=False):
            n = str(r[0]).strip().replace(" kraj", "")
            if n in KR:
                flows[y][n] = [int(float(v)) for v in r[1:12]]
        if f == files[-1]:
            cur = None
            for r in pd.read_excel(x, sheet_name=sheet("T5"), header=None).itertuples(index=False):
                c, s = chapter_key(r[0]), re.sub(r"\s+", " ", str(r[0])).strip()
                if c and c != "ALL":
                    cur = c
                elif cur and "(" in s and num(r[1]) is not None:
                    dg.setdefault(cur, []).append([s, num(r[1]), num(r[4]), num(r[7]), num(r[9])])
    dg = {c: sorted(v, key=lambda g: -g[1])[:10] for c, v in dg.items()}
    return hs, pop, flows, chn, dg


AGE_BINS = ["00", "01-04", "05-14", "15-24", "25-34", "35-44", "45-54", "55-64", "65-74", "75-84", "85_v"]
ROMAN_CH = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII", "XIII", "XIV", "XV", "XVI", "XVII", "XVIII", "XIX", "XX", "XXI", "XXII"]
MIN_CODE_HOSP = 30  # 3-digit codes below this yearly maximum in SR are only counted within their group


def diagnoses():
    """Hospitalizations by ICD-10 code x facility region and by code x sex x age, 2020+."""
    files = sorted(glob.glob(str(DATA / "nczi_diagnozy" / "*.xlsx")))
    dataset = lambda f: pd.read_excel(f, sheet_name=next(s for s in pd.ExcelFile(f).sheet_names if s.startswith("Dataset")), dtype=str)
    terr = [SR] + [k + " kraj" for k in KR]
    code_group, groups, codes = {}, {}, {}
    age = {"ch": {}, "gr": {}, "cd": {}}
    for f in [f for f in files if "diagnoza_vek" in f]:
        v = dataset(f)
        v = v.rename(columns={c: "HOSP" for c in v.columns if c.startswith("HOSP")})
        v["HOSP"] = pd.to_numeric(v["HOSP"], errors="coerce").fillna(0)
        v = v[v.VEK_SKUP_10.isin(AGE_BINS)]
        y = v.ROK_SPRAC.iloc[0]
        v["ch"] = v.DIAG_HOSP_KAP.map(lambda c: ROMAN_CH[int(c) - 1])
        for r in v[["DIAG_HOSP_OD", "DIAGNOZA_POPIS", "DIAG_HOSP_SKUP", "DIAG_SKUP_POPIS", "ch"]].drop_duplicates("DIAG_HOSP_OD").itertuples(index=False):
            code_group[r[0]] = r[2]
            codes.setdefault(r[0], {"n": " ".join(str(r[1]).split())})
            groups.setdefault(r[2], {"n": " ".join(str(r[3]).split()).replace(" - ", "–").replace("( ", "(").replace(" )", ")"), "c": r[4]})
        v["col"] = v.POHLAVIE.map({"1": 0, "2": 1}) * len(AGE_BINS) + v.VEK_SKUP_10.map(AGE_BINS.index)
        v = v.dropna(subset=["col"])
        for level, key in [("ch", "ch"), ("gr", "DIAG_HOSP_SKUP"), ("cd", "DIAG_HOSP_OD")]:
            for k, s in v.groupby(key):
                arr = [0] * (2 * len(AGE_BINS))
                for c, h in s.groupby("col")["HOSP"].sum().items():
                    arr[int(c)] = int(h)
                age[level].setdefault(k, {})[y] = arr
        allv = [0] * (2 * len(AGE_BINS))
        for c, h in v.groupby("col")["HOSP"].sum().items():
            allv[int(c)] = int(h)
        age["ch"].setdefault("ALL", {})[y] = allv
    uz = {"ch": {}, "gr": {}, "cd": {}}
    for f in [f for f in files if "uzemie" in f]:
        d = dataset(f)
        y = d.ROK_SPRAC.iloc[0]
        for c in ["HOSP_SPOLU", "DLHOSP_SPOLU", "UMRTIA_SPOLU"]:
            d[c] = pd.to_numeric(d[c], errors="coerce").fillna(0).astype(int)
        d["t"] = d.UZEMIEZZ_POPIS.str.strip().map(lambda s: terr.index(s) if s in terr else -1)
        d = d[d.t >= 0]
        def put(level, key, rows):
            arr = [0] * (3 * len(terr))
            for r in rows.itertuples(index=False):
                arr[3 * r.t:3 * r.t + 3] = [int(r.HOSP_SPOLU), int(r.DLHOSP_SPOLU), int(r.UMRTIA_SPOLU)]
            uz[level].setdefault(key, {})[y] = arr
        put("ch", "ALL", d[d.DIAGNOZA_AGR == "SP"])
        for c, s in d[d.DIAGNOZA_AGR == "KPT"].groupby("DIAGNOZA_KOD"):
            put("ch", ROMAN_CH[int(c) - 1], s)
        kod = d[d.DIAGNOZA_AGR == "KOD"]
        for c, s in kod.groupby("DIAGNOZA_KOD"):
            put("cd", c, s)
        kod = kod.assign(g=kod.DIAGNOZA_KOD.map(code_group))
        for g, s in kod.dropna(subset=["g"]).groupby("g"):
            s = s.groupby("t", as_index=False)[["HOSP_SPOLU", "DLHOSP_SPOLU", "UMRTIA_SPOLU"]].sum()
            put("gr", g, s)
    keep = {c for c, ys in uz["cd"].items() if max(a[0] for a in ys.values()) >= MIN_CODE_HOSP and c in code_group}
    out = {"bins": AGE_BINS, "ch": {}, "gr": {}, "cd": {}}
    for c in uz["ch"]:
        out["ch"][c] = {"uz": uz["ch"][c], "age": age["ch"].get(c, {})}
    for g, meta in groups.items():
        if g in uz["gr"]:
            out["gr"][g] = {**meta, "uz": uz["gr"][g], "age": age["gr"].get(g, {})}
    for c in sorted(keep):
        out["cd"][c] = {**codes[c], "g": code_group[c], "uz": uz["cd"][c], "age": age["cd"].get(c, {})}
    return out


TECH = {"laparoskopicky": "laparoskopicky", "roboticky": "roboticky", "otvorene": "otvorene", "klasicky": "klasicky", "laparotomicky": "laparotomicky"}


def surgery():
    """NCZI surgical statistics 2013+: operations (P02), day surgery (J01), surgical outpatient clinics (A12)."""
    src = DATA / "nczi_chirurgia"
    terr = [SR] + [k + " kraj" for k in KR]
    ti = lambda s: terr.index(str(s).strip()) if str(s).strip() in terr else -1
    nz = lambda s: pd.to_numeric(s, errors="coerce").fillna(0)

    op = pd.read_excel(src / "P02_2013_2024_dataset.xlsx", sheet_name="SUM_3602_OZ")
    op["t"] = op.UZEMIE_POPIS.map(ti)
    op = op[op.t >= 0]
    for c in ["OPER_0018", "OPER_19", "P_OPER_0018", "P_OPER_19", "P_OPER_UMR_0018", "P_OPER_UMR_19"]:
        op[c] = nz(op[c])
    op["n"] = op.OPER_0018 + op.OPER_19
    op["pat"] = op.P_OPER_0018 + op.P_OPER_19
    op["umr"] = op.P_OPER_UMR_0018 + op.P_OPER_UMR_19
    op["y"] = op.ROK_SPRAC.astype(str)
    op["g"] = op.CISV_OPERACIE_1.astype(str).str.zfill(2)
    op["o"] = op.CISV_OPERACIE_2.astype(str)
    years = sorted(op.y.unique())
    last = years[-1]

    def terr_series(df):
        out = {}
        for (y, t), n in df.groupby(["y", "t"]).n.sum().items():
            out.setdefault(y, [0] * 9)[t] = int(n)
        return out

    def sr_series(df):
        s = df[df.t == 0].groupby("y")[["pat", "umr", "OPER_0018"]].sum()
        return {y: [int(r.pat), int(r.umr), int(r.OPER_0018)] for y, r in s.iterrows()}

    groups = {g: {"n": " ".join(str(s.CISV_OPERACIE_1_POP.iloc[-1]).split()), "t": terr_series(s), "sr": sr_series(s)} for g, s in op.groupby("g")}
    ops = {}
    for o, s in op.groupby("o"):
        dep = {}
        for (d, t), n in s[s.y == last].groupby(["ODB_ZAM_UTV_POPIS", "t"]).n.sum().items():
            if n:
                dep.setdefault(str(d).strip(), [0] * 9)[t] = int(n)
        ops[o] = {"n": " ".join(str(s.CISV_OPERACIE_2_POP.iloc[-1]).split()), "g": s.g.iloc[-1], "t": terr_series(s), "sr": sr_series(s), "dep": dep}
    tech = {}
    for o, v in ops.items():
        parts = v["n"].rsplit(" - ", 1)
        if len(parts) == 2 and parts[1].strip() in TECH:
            tech.setdefault(parts[0], []).append([o, TECH[parts[1].strip()]])
    tech = [{"base": b, "g": ops[items[0][0]]["g"], "items": sorted(items, key=lambda i: i[1])} for b, items in tech.items() if len(items) >= 2]

    em = pd.read_excel(src / "P02_2013_2024_dataset.xlsx", sheet_name="SUM_3234")
    em["t"] = em.UZEMIE_POPIS.map(ti)
    em = em[em.t >= 0]
    for c in ["P_OPER_0_5H", "P_OPER_6H", "P_OPER_0_5H_UMR", "P_OPER_6H_UMR"]:
        em[c] = nz(em[c])
    em["umr"] = em.P_OPER_0_5H_UMR + em.P_OPER_6H_UMR
    em["c"] = em.CISV_CHIR_NEODKL_2.astype(str).str.zfill(4)
    ecats = {c: " ".join(str(s.CISV_CHIR_NEODKL_2_P.iloc[-1]).split()) for c, s in em.groupby("c")}
    emd = {}
    for (y, c, t), s in em.groupby([em.ROK_SPRAC.astype(str), "c", "t"]):
        a = emd.setdefault(y, {}).setdefault(c, [0] * 27)
        a[3 * t:3 * t + 3] = [int(s.P_OPER_0_5H.sum()), int(s.P_OPER_6H.sum()), int(s.umr.sum())]

    jp = pd.read_excel(src / "J01_2013_2024_dataset.xlsx", sheet_name="SUM_2301")
    places = {}
    for r in jp.itertuples(index=False):
        t = ti(r.UZEMIE_POPIS)
        if t >= 0:
            places.setdefault(str(r.ROK_SPRAC), [0] * 9)[t] = int(nz(pd.Series([r.MIES_P]))[0])
    jv = pd.read_excel(src / "J01_2013_2024_dataset.xlsx", sheet_name="SUM_3602_OZ")
    jv["t"] = jv.UZEMIE_POPIS.map(ti)
    jv = jv[jv.t >= 0]
    jv["n"] = nz(jv.P_OPE_0018) + nz(jv.P_OPE_19)
    jv["y"] = jv.ROK_SPRAC.astype(str)
    jv["cat"] = jv.CISV_J1_1_POPIS.where(jv.CISV_J1_1_POPIS.notna(), jv.CIS_VYK_J1_DRG_SK1_P).astype(str).map(lambda s: " ".join(s.replace("\xa0", " ").split()))
    jtot, jcat = terr_series(jv), {}
    for (y, c, t), n in jv.groupby(["y", "cat", "t"]).n.sum().items():
        if n:
            jcat.setdefault(y, {}).setdefault(c, [0] * 9)[t] = int(n)

    am = pd.read_excel(src / "A12_2013_2024_dataset.xlsx", sheet_name="SUM_3101-3602")
    labels = pd.read_excel(src / "A12_2013_2024_dataset.xlsx", sheet_name="Struktura_datasetu").set_index("Kód položky")["Názov položky"]
    bases = []
    for c in am.columns:
        if c.startswith(("NAV_", "VYK_")) and not c.endswith(("_0018", "_00")):
            base = c[: -len("_19")]
            kid = next(k for k in am.columns if k.startswith(base + "_") and k != c)
            nm = re.sub(r"\s*(u pacientov\s*)?vo veku.*$", "", str(labels[c])).replace("Chirurgických výkonov pre ", "").replace("Počet chirurgických výkonov pre ", "").replace("Počet výkonov - ", "").replace("Počet výkonov pre ", "").replace("Počet ", "")
            bases.append((c, kid, nm[0].upper() + nm[1:]))
    amd = {}
    for r in am.to_dict("records"):
        t = ti(r["UZEMIE_POPIS"])
        if t < 0:
            continue
        a = amd.setdefault(str(r["ROK_SPRAC"]), [0] * (9 * len(bases)))
        for i, (c, kid, _) in enumerate(bases):
            v = sum(float(x) for x in (r[c], r[kid]) if pd.notna(x))
            a[i * 9 + t] = int(v)
    return {"years": years, "groups": groups, "ops": ops, "tech": tech, "last": last,
            "em": {"cats": ecats, "d": emd}, "jzs": {"places": places, "tot": jtot, "cat": jcat},
            "amb": {"labels": [b[2] for b in bases], "d": amd}}


# SAR department code -> (Slovak name, hospital code from the 2026 categorization or None, region)
SAR_DEPTS = {
    "BA.BORY": ("Nemocnica Bory", "P25534", "Bratislavský"), "BA.DOK": ("Národný ústav detských chorôb", "P43059", "Bratislavský"),
    "BA.I.OTK": ("UN Bratislava, I. ortopedicko-traumatologická klinika", "P40707", "Bratislavský"),
    "BA.II.OTK": ("UN Bratislava, II. ortopedicko-traumatologická klinika", "P40707", "Bratislavský"),
    "BA.MED": ("Nemocnica Medissimo", None, "Bratislavský"), "BA.NPTM": ("Nemocnica Novapharm", "P84713", "Bratislavský"),
    "BA.NSM": ("UN – Nemocnica svätého Michala", "P36845", "Bratislavský"), "BA.S.E": ("Sport & Endo Clinic", None, "Bratislavský"),
    "BA.TRAUM": ("UN Bratislava, traumatológia", "P40707", "Bratislavský"), "MA.TRAUM": ("Nemocnica Malacky", "P29189", "Bratislavský"),
    "DS.ORTH": ("Nemocnica Dunajská Streda", "P51102", "Trnavský"), "GA.TRAUM.ORTH": ("Nemocnica sv. Lukáša Galanta", "P80747", "Trnavský"),
    "PN.ORTH": ("Nemocnica A. Wintera Piešťany", "P93083", "Trnavský"), "SI.ORTH": ("FN AGEL Skalica", "P81264", "Trnavský"),
    "TT.TRAUM.ORTH": ("FN Trnava", "P20979", "Trnavský"),
    "PB.ORTH": ("Nemocnica Považská Bystrica", "P50945", "Trenčiansky"), "PD.ORTH.TRAUM": ("Nemocnica Prievidza (Bojnice)", "P51373", "Trenčiansky"),
    "PE.TRAUM": ("Mestská nemocnica Partizánske", None, "Trenčiansky"), "TN.ORTH": ("FN Trenčín, ortopédia", "P42383", "Trenčiansky"),
    "TN.TRAUM": ("FN Trenčín, traumatológia", "P42383", "Trenčiansky"),
    "LV.ORTH.": ("Nemocnica AGEL Levice, ortopédia", "P01675", "Nitriansky"), "LV.TRAUM": ("Nemocnica AGEL Levice, traumatológia", "P01675", "Nitriansky"),
    "NR.TRAUM.ORTH": ("FN Nitra", "P85687", "Nitriansky"), "NZ.ORTH": ("FN Nové Zámky, ortopédia", "P81095", "Nitriansky"),
    "NZ.TRAUM": ("FN Nové Zámky, traumatológia", "P81095", "Nitriansky"), "TO.ORTH": ("Nemocnica Topoľčany, ortopédia", "P59688", "Nitriansky"),
    "TO.TRAUM": ("Nemocnica Topoľčany, traumatológia", "P59688", "Nitriansky"),
    "BB.ORTH": ("FNsP F. D. Roosevelta Banská Bystrica, ortopédia", "N42231", "Banskobystrický"),
    "BB.TRAUM": ("FNsP F. D. Roosevelta Banská Bystrica, traumatológia", "N42231", "Banskobystrický"),
    "LC.ORTH.TRAUM": ("Nemocnica Lučenec", "N50139", "Banskobystrický"), "ZV.ORTH.TRAUM": ("Nemocnica AGEL Zvolen", "P79469", "Banskobystrický"),
    "DK.ORTH.TRAUM": ("Dolnooravská nemocnica Dolný Kubín", "P51283", "Žilinský"), "LM.TRAUM.ORTH": ("Liptovská nemocnica Liptovský Mikuláš", "P66051", "Žilinský"),
    "MT.ORTH": ("UN Martin", "P38811", "Žilinský"), "RK.TRAUM.ORTH": ("ÚVN SNP Ružomberok", "P91151", "Žilinský"),
    "TS.TRAUM": ("Hornooravská nemocnica Trstená", "P46405", "Žilinský"), "ZA.ORTH": ("FNsP Žilina, ortopédia", "N92725", "Žilinský"),
    "ZA.TRAUM": ("FNsP Žilina, traumatológia", "N92725", "Žilinský"),
    "HE.ORTH": ("Nemocnica A. Leňa Humenné", "P27233", "Prešovský"), "PO.ORTH": ("FNsP J. A. Reimana Prešov, ortopédia", "N33067", "Prešovský"),
    "PO.TRAUM": ("FNsP J. A. Reimana Prešov, traumatológia", "N33067", "Prešovský"), "PP.ORTH": ("Nemocnica Poprad, ortopédia", "N22001", "Prešovský"),
    "PP.TRAUM": ("Nemocnica Poprad, traumatológia", "N22001", "Prešovský"), "SL.TRAUM": ("Ľubovnianska nemocnica", "N56229", "Prešovský"),
    "VT.TRAUM": ("Vranovská nemocnica", "P02824", "Prešovský"),
    "KE.ORTH": ("Železničné zdravotníctvo Košice", "P45507", "Košický"), "KE.ORTH.TRAUM": ("UN L. Pasteura Košice, ortopédia", "P77017", "Košický"),
    "KE.TRAUM": ("UN L. Pasteura Košice, traumatológia", "P77017", "Košický"), "KS.ORTH": ("Nemocnica AGEL Košice-Šaca", "P43979", "Košický"),
    "MI.ORTH": ("Nemocnica Š. Kukuru Michalovce, ortopédia", "P66599", "Košický"), "MI.TRAUM": ("Nemocnica Š. Kukuru Michalovce, traumatológia", "P66599", "Košický"),
    "RV.TRAUM": ("Nemocnica sv. Barbory Rožňava", "P85363", "Košický"),
}


def sar():
    """Slovak Arthroplasty Register annual report (PDF): hip and knee arthroplasty."""
    import pymupdf
    pdf = sorted((DATA / "sar").glob("SAR_vyrocna_sprava_*.pdf"))[-1]
    doc = pymupdf.open(pdf)
    texts = [p.get_text() for p in doc]
    page_of = lambda n: next(i for i, t in enumerate(texts) if re.search(rf"Tab\. ?{n} ", t))
    clean = lambda s: " ".join(str(s or "").replace("Hy brids", "Hybrids").replace("Rev erse hy br", "Reverse hybr").split())
    axis = lambda s: bool(re.fullmatch(r"[\d\s%.,]+", s))

    def table(n, must):
        for tb in doc[page_of(n)].find_tables().tables:
            rows = tb.extract()
            for i, row in enumerate(rows[:3]):
                head = [clean(c) for c in row]
                if must in head:
                    return head, rows[i + 1:]
        raise ValueError(f"SAR table {n}: header {must!r} not found")

    def by_year(n, must):
        head, rows = table(n, must)
        yi = next(i for i, h in enumerate(head) if h in ("Year", "Years"))
        cols = [(i, h) for i, h in enumerate(head) if h and i != yi and not axis(h)]
        d = {}
        for r in rows:
            y = clean(r[yi])
            if re.fullmatch(r"\d{4}", y):
                d[y] = [int(float(clean(r[i]) or 0)) for i, _ in cols]
        return {"labels": [h for _, h in cols], "d": d}

    def rr(n):
        head, rows = table(n, "Fixation")
        return [[clean(r[1]), int(clean(r[2])), int(clean(r[3])), float(clean(r[4])), float(clean(r[7]))] for r in rows if clean(r[1]) and clean(r[2]).isdigit()]

    def depts(n):
        out, p = [], page_of(n)
        for page in (p, p + 1):  # long tables continue on the next page
            for tb in doc[page].find_tables().tables:
                rows = tb.extract()
                if clean(rows[0][0]) != "Department":
                    continue
                for r in rows[1:]:
                    c = clean(r[0])
                    if c == "Total":
                        return out
                    if c and clean(r[2]).isdigit():
                        out.append([c, int(clean(r[2])), int(clean(r[3]))])
        raise ValueError(f"SAR table {n}: no Total row")

    year = re.search(r"(\d{4})", pdf.name).group(1)
    joints = {
        "hip": dict(pr=by_year(18, "Primary THA"), pop=by_year(10, "Inhabitants"), sex=by_year(11, "Females"), age=by_year(26, "[0,55]"),
                    diag=by_year(36, "Primary OA"), fix=by_year(46, "Cemented"), rr=rr(47), cemA=by_year(50, "Copal"),
                    cemN=by_year(51, "Osteobond"), reas=by_year(64, "Luxation"), dep=depts(53)),
        "knee": dict(pr=by_year(85, "Primary TKA"), sex=by_year(14, "Females"), age=by_year(93, "[0,55]"),
                     diag=by_year(103, "Primary monocond.OA"), fix=by_year(113, "Cemented"), rr=rr(114), cemA=by_year(117, "Copal"),
                     cemN=by_year(118, "Osteobond"), reas=by_year(130, "Early Infection"), dep=depts(119)),
    }
    for j in joints.values():
        unknown = [d[0] for d in j["dep"] if d[0] not in SAR_DEPTS]
        if unknown:
            raise ValueError(f"SAR departments without mapping: {unknown}")
    return {"year": year, "j": joints, "depts": {k: list(v) for k, v in SAR_DEPTS.items()}}


def main():
    stats, years = network()
    hosp, groups = hospitals()
    hs, pop, flows, chn, dg = hospitalizations()
    dx = diagnoses()
    sx = surgery()
    ar = sar()
    data = {"groups": groups, "stats": stats, "hosp": hosp, "shapes": shapes(), "years": years,
            "hs": hs, "popY": pop, "flows": flows, "chn": chn, "dg": dg, "dx": dx, "sx": sx, "ar": ar, "hyears": sorted(pop)}
    page = (ROOT / "template.html").read_text(encoding="utf-8").replace("__DATA__", json.dumps(data, ensure_ascii=False, separators=(",", ":")))
    # template.html is an artifact body; a standalone host needs the document shell (charset!) around it
    head_end = page.index("</style>") + len("</style>")
    html = ('<!doctype html>\n<html lang="sk">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
            '<style>html,body{margin:0}</style>\n' + page[:head_end] + "\n</head>\n<body>\n" + page[head_end:] + "\n</body>\n</html>\n")
    (ROOT / "public").mkdir(exist_ok=True)
    (ROOT / "public" / "index.html").write_text(html, encoding="utf-8")
    print(f"public/index.html: {len(html) // 1024} kB, years {years[0]}–{years[-1]} / {sorted(pop)[0]}–{sorted(pop)[-1]}, {len(hosp)} hospitals")


if __name__ == "__main__":
    main()
