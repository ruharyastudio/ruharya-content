#!/usr/bin/env python3
"""Ruharya yayın öncesi tekrar / benzerlik denetimi (yalnızca standart kütüphane, yerel, ağsız).

Ali'nin 24 Kasım 2026 kararı:
  1. Aynı alt konu, teknik ya da anlatım yeni başlıkla bile yeniden kullanılmaz (aynı geniş kaynak, gerçekten
     farklı bir alt konu için kullanılabilir).
  2. Haftalık özet / recap gönderisi yok.
  3. Reels, önceki carousel'in metnini ya da sorularını taşımaz; bağımsız ve yeni içeriktir.
  4. Yayın öncesi zorunlu denetim; tekrar varsa Buffer'a gönderilmez.

Kullanım:
  python3 tools/tekrar_denetimi.py content/YYYY-MM-DD-konu.json            # carousel (+ .caption.txt)
  python3 tools/tekrar_denetimi.py content/YYYY-MM-DD-konu.reel.json       # Reels (+ .reel.caption.txt)
  seçenekler: --gecmis-dizin DIR (varsayılan: aday dosyanın dizini)   --json (yalnızca JSON yaz)
              --cikti DOSYA (JSON raporu ayrıca dosyaya yaz)          --tum-ciftler (ayar/hata ayıklama)
Çıkış kodu: 0 = geçti, 1 = tekrar tespit edildi (ENGEL), 2 = denetim yapılamadı (eksik/bozuk girdi; bu da ENGELdir).

Geçmiş: aynı dizindeki, adayla aynı ya da önceki tarihli, `taslak-` önekli olmayan tüm içerikler (adayın kendisi hariç).
Aynı gün/aynı konu klasörü (ör. aynı gün hem carousel hem Reels) birbirinin geçmişidir.

Normalizasyon: Türkçe I/İ/ı, aksan ve Sanskritçe/Pāli işaretleri (ā ṇ ś ṭ ḥ ū ī ...), HTML etiketleri, noktalama atılır;
`sh`→`s`; sözcükler 5 harfe kısaltılır (Türkçe ekleri kabaca yutmak için). Yalnızca genel sözcükler (nefes, Ruharya,
bağlaçlar), zorunlu güvenlik notu, standart CTA ve standart hashtag'ler benzerliğe sayılmaz.
"""
import argparse
import json
import math
import re
import sys
import unicodedata
from pathlib import Path

# ---------------------------------------------------------------- normalizasyon
def norm(metin):
    t = re.sub(r"<[^>]+>", " ", metin or "")
    t = t.replace("İ", "i").replace("I", "ı").lower()
    t = unicodedata.normalize("NFKD", t)
    t = "".join(c for c in t if not unicodedata.combining(c))
    t = t.replace("ı", "i").replace("ø", "o").replace("đ", "d").replace("ł", "l")
    t = t.replace("sh", "s")  # śodhana / shodhana
    return re.sub(r"[^a-z0-9]+", " ", t).strip()


STOP = set("""
ve ile bir bu su o da de mi mu ki icin gibi daha en cok her ne nasil nerede neden hangi hangisi olarak olan olur olursa
ise ama ya veya hem ben sen biz siz sana sende bana beni seni kendi kendine bugun dun yarin simdi sonra once artik
sadece yalniz yani ancak bile kadar gore diye mi mu var yok olan olur oldu olmak etmek edilir eder eden ettigi
bazen hep hic hala zaten belki sey seyi seyler kisi kisiler birine birini birinin ilk son iki uc dort bes alti yedi
sekiz dokuz on bunu bunun buna bundan sunu onu onun ona ondan bunlar onlar orada burada ayni baska diger tum
bu hafta gun yil kez kere biraz fazla az mutlaka dikkat sorun ayrica ise iken ken dir dur tir tur
atlas no seri pratik ogreti
""".split())
# 'nefes' kökü, marka ve çok genel sözcükler: tek başına benzerlik sayılmaz
GENEL_KOK = ("nefes", "ruhar", "soluk")
GENEL = set("""
nefes ruharya ruharyanefes farkindalik farkinda mindfulness meditasyon breathwork pratigi pratik uygulama
gonderi kaydet kaydir yorum yorumlara profil profilde link sorular soru ozet kart
""".split())
STANDART_ETIKET = set("""
ruharyanefes ruharya nefes nefesfarkindaligi nefespratigi farkindalik mindfulness meditasyon breathwork nefesegitimi
nefesegzersizi icsessizlik kendinitani
""".split())

# Zorunlu güvenlik notu ve standart CTA cümleleri benzerliğe sayılmaz (norm() sonrası aranır)
BOILER = re.compile(
    r"\b(rahatsizlik|bas donmesi|baş donmesi|doktor|hekim|tibbi|saglik sorun|saglik durum|hamile|zorlama|"
    r"kaydet|gonder|yorumlara|yorumlar|yorum yaz|kaydir|profildeki|profilimiz|begen|takip|"
    r"kendi pratigine baslamak|ruharya nefes|uygulamasi|sabitlenmis)\b"
    # standart oturuş/postür talimatı da pratikler arasında ortak kalıptır
    r"|\bdik otur|\bomuz\w* gevs|\brahat (bir )?(otur|pozisyon)|\bsandalyede\b")


def kok(t):
    return t[:5] if len(t) > 5 else t


def genel_mi(t):
    return t in STOP or t in GENEL or t.startswith(GENEL_KOK) or len(t) < 3 or t.isdigit()


def cumleler(metin):
    parcalar = re.split(r"<br\s*/?>|[\n.!?;]+", metin or "")
    return [p for p in parcalar if p and p.strip()]


def kok_dizisi(metin):
    """Metni içerik köklerine çevirir (genel sözcükler atılır)."""
    return [kok(t) for t in norm(metin).split() if not genel_mi(t)]


def temiz_cumleler(metin):
    """Güvenlik notu / CTA cümlelerini atar; kalan cümlelerin kök dizilerini döndürür."""
    out = []
    for c in cumleler(metin):
        if BOILER.search(norm(c)):
            continue
        k = kok_dizisi(c)
        if k:
            out.append(k)
    return out


# ---------------------------------------------------------------- içerik okuma
class Alan:
    __slots__ = ("ad", "tur", "ham", "cumle")

    def __init__(self, ad, tur, ham):
        self.ad, self.tur, self.ham = ad, tur, ham
        # tur: baslik | govde | soru | kaynak | aciklama | etiket
        self.cumle = [] if tur in ("kaynak", "etiket") else temiz_cumleler(ham)


def _slayt_alanlari(d):
    out = []
    for i, s in enumerate(d.get("slides") or []):
        for k in ("kicker", "title", "lead"):
            if s.get(k):
                out.append(Alan(f"slides[{i}].{k}", "baslik", s[k]))
        b = s.get("body")
        for j, x in enumerate(b if isinstance(b, list) else ([b] if b else [])):
            out.append(Alan(f"slides[{i}].body[{j}]", "govde", x))
        for j, x in enumerate(s.get("steps") or []):
            out.append(Alan(f"slides[{i}].steps[{j}]", "soru" if s.get("kind") == "steps" else "govde", x))
        if s.get("note"):
            out.append(Alan(f"slides[{i}].note", "govde", s["note"]))
        if s.get("src"):
            out.append(Alan(f"slides[{i}].src", "kaynak", s["src"]))
    return out


def _reel_alanlari(d):
    out = []
    a, b = d.get("a") or {}, d.get("b") or {}
    for k in ("kicker", "title"):
        if a.get(k):
            out.append(Alan(f"a.{k}", "baslik", a[k]))
    for j, q in enumerate(a.get("questions") or []):
        out.append(Alan(f"a.questions[{j}]", "soru", q))
    if a.get("foot"):
        out.append(Alan("a.foot", "govde", a["foot"]))
    for k in ("kicker", "title"):
        if b.get(k):
            out.append(Alan(f"b.{k}", "baslik", b[k]))
    if b.get("body"):
        out.append(Alan("b.body", "govde", b["body"]))
    return out


def _aciklama_alanlari(metin):
    out, govde = [], []
    for ln in metin.splitlines():
        if ln.strip().startswith("#"):
            for h in re.findall(r"#(\w+)", ln):
                if norm(h).replace(" ", "") not in STANDART_ETIKET:
                    out.append(Alan(f"caption.hashtag#{h}", "etiket", h))
        else:
            govde.append(ln)
    for j, par in enumerate(p for p in "\n".join(govde).split("\n\n") if p.strip()):
        out.append(Alan(f"caption.paragraf[{j}]", "aciklama", par))
    return out


class Icerik:
    def __init__(self, yol, aciklama_zorunlu=True):
        self.yol = Path(yol)
        self.ad = self.yol.name
        self.reel = self.yol.name.endswith(".reel.json")
        taban = self.yol.name[: -len(".reel.json" if self.reel else ".json")]
        self.taban = taban
        m = re.match(r"(?:taslak-)?(\d{4}-\d{2}-\d{2})", taban)
        self.tarih = m.group(1) if m else ""
        self.taslak = taban.startswith("taslak-")
        d = json.loads(self.yol.read_text(encoding="utf-8"))
        self.alanlar = _reel_alanlari(d) if self.reel else _slayt_alanlari(d)
        self.slayt_sayisi = len(d.get("slides") or [])
        self.aciklama_yolu = self.yol.with_name(taban + (".reel.caption.txt" if self.reel else ".caption.txt"))
        if self.aciklama_yolu.exists():
            self.alanlar += _aciklama_alanlari(self.aciklama_yolu.read_text(encoding="utf-8"))
        elif aciklama_zorunlu:
            raise FileNotFoundError(f"açıklama dosyası yok: {self.aciklama_yolu}")
        if not any(a.tur in ("govde", "soru") for a in self.alanlar):
            raise ValueError(f"{self.ad}: denetlenecek metin yok")
        self.baslik_cumle = [a for a in self.alanlar if a.tur == "baslik"]

    @property
    def etiket_kokleri(self):
        return {kok(t) for a in self.alanlar if a.tur == "etiket" for t in norm(a.ham).split()}

    def cekirdek(self):
        """(kök kümesi, bigram kümesi): kaynak künyeleri, CTA ve standart hashtag hariç."""
        k, bg = set(), set()
        for a in self.alanlar:
            if a.tur == "kaynak":
                continue
            for dizi in a.cumle:
                k.update(dizi)
                bg.update(zip(dizi, dizi[1:]))
        return k, bg

    def kaynak_kokleri(self):
        s = set()
        for a in self.alanlar:
            if a.tur == "kaynak":
                s.update(kok_dizisi(a.ham))
        return s

    def metin_parcalari(self):
        return [(a.ad, a.tur, a.ham) for a in self.alanlar if a.tur != "etiket"]


# ---------------------------------------------------------------- eşikler
ESIK_ALT_KONU = 0.25         # IDF ağırlıklı ortak çekirdek oranı
MIN_NADIR_KOK = 3            # ... ve en az bu kadar nadir ortak kök
MIN_NADIR_BIGRAM = 2         # ... ve en az bu kadar nadir ortak ardışık ikili (aynı anlatım izi)
ESIK_ALT_KONU_AYNI_KAYNAK = 0.15  # aynı kaynak eseri (>=2 ortak künye kökü) + ortak ikili: eşik düşer
MIN_ORTAK_KAYNAK = 2
ESIK_ALT_KONU_YUKSEK = 0.45  # bu orandan sonra ikili şartı aranmaz
ESIK_SORU = 0.60             # iki sorunun kök Jaccard benzerliği
MIN_SORU = 2                 # bu kadar soru eşleşirse "aynı soru listesi"
ESIK_BASLIK = 0.75           # başlık kökleri Jaccard (≥2 içerik kökü) → aynı başlık
RECAP_KAC_ESLESME = 3        # aday ≥ bu kadar farklı eski içerikle alt konu eşiğini geçiyorsa derleme/özet

RECAP_KALIPLARI = [
    (r"\bhaftanin ozeti\b", "haftanın özeti"),
    (r"\bhaftalik ozet\b", "haftalık özet"),
    (r"\bhafta(nin)? (toparlam|tekrar|recap)", "hafta toparlaması"),
    (r"\bgecen hafta(ki)?\b", "geçen hafta"),
    (r"\bbu hafta \w*\s*(konustuk|gorduk|ogrendik|paylastik|isledik|isledigimiz)\b", "bu hafta konuştuk/öğrendik"),
    (r"\b(alti|bes|dort|uc|yedi) gonderi\b", "N gönderi özeti"),
    (r"\brecap\b|\bozetleyelim\b|\byeniden hatirlayalim\b|\bgeri donelim\b|\bhizlica tekrar\b", "recap dili"),
]


def _idf(df, n):
    return math.log((n + 1) / (df + 0.5)) + 1.0


class Bulgu(dict):
    pass


# ---------------------------------------------------------------- denetim çekirdeği
def _duz(ham, uz=90):
    t = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", ham)).strip()
    return t if len(t) <= uz else t[: uz - 1] + "…"


def _alan_bul(icerik, anahtarlar):
    ks = set()
    for a in anahtarlar:
        ks.update(a if isinstance(a, tuple) else (a,))
    en, ad = 0, "-"
    for a in icerik.alanlar:
        if a.tur in ("kaynak", "etiket"):
            continue
        sayi = len(ks & set(sum(a.cumle, [])))
        if sayi > en:
            en, ad = sayi, a.ad
    return ad


class Korpus:
    """Aday + geçmiş üzerinde IDF/df hesapları."""

    def __init__(self, aday, gecmis):
        self.aday, self.gecmis = aday, gecmis
        self.belgeler = gecmis + [aday]
        self.n = len(self.belgeler)
        self.cek = {id(i): i.cekirdek() for i in self.belgeler}
        self.df_k, self.df_b = {}, {}
        for i in self.belgeler:
            k, bg = self.cek[id(i)]
            for t in k:
                self.df_k[t] = self.df_k.get(t, 0) + 1
            for b in bg:
                self.df_b[b] = self.df_b.get(b, 0) + 1
        self.nadir = max(3, self.n // 6)  # bir kök en çok bu kadar içerikte geçiyorsa "nadir"

    def cift(self, h):
        """Aday ile h arasında ölçüler; kaynak künyesi sözcükleri (ör. majjhima, openstax) ortaklıktan sayılmaz."""
        a = self.aday
        kaynak = a.kaynak_kokleri() | h.kaynak_kokleri()
        ak, abg = self.cek[id(a)]
        hk, hbg = self.cek[id(h)]
        ak, hk = ak - kaynak, hk - kaynak
        abg = {b for b in abg if not set(b) & kaynak}
        hbg = {b for b in hbg if not set(b) & kaynak}

        def agirlik(kume):
            return sum(_idf(self.df_k[t], self.n) for t in kume)

        ortak = ak & hk
        oran = agirlik(ortak) / (min(agirlik(ak), agirlik(hk)) or 1.0)
        nadir_ortak = sorted((t for t in ortak if self.df_k[t] <= self.nadir), key=lambda t: (self.df_k[t], t))
        nadir_bigram = sorted(b for b in (abg & hbg) if self.df_b[b] <= self.nadir)
        ortak_kaynak = sorted(a.kaynak_kokleri() & h.kaynak_kokleri())
        return dict(oran=oran, nadir_ortak=nadir_ortak, nadir_bigram=nadir_bigram, ortak_kaynak=ortak_kaynak)


def alt_konu_tekrari_mi(c):
    if len(c["nadir_ortak"]) < MIN_NADIR_KOK:
        return False
    if c["oran"] >= ESIK_ALT_KONU_YUKSEK:
        return True
    if c["oran"] >= ESIK_ALT_KONU and len(c["nadir_bigram"]) >= MIN_NADIR_BIGRAM:
        return True
    # Aynı kaynak eseri (ör. aynı sutta) + aynı anlatım izi: künye sözcükleri ortaklıktan düşüldüğü için oran düşük kalır
    return (len(c["ortak_kaynak"]) >= MIN_ORTAK_KAYNAK and c["oran"] >= ESIK_ALT_KONU_AYNI_KAYNAK
            and len(c["nadir_bigram"]) >= MIN_NADIR_BIGRAM)


def denetle(aday, gecmis):
    """Döndürür: bulgular listesi. Boş liste = geçti."""
    kor = Korpus(aday, gecmis)
    bulgular = []

    # 1. Recap/haftalık özet dili (adayın kendi metninde; kaynak künyeleri hariç)
    gorulen = set()
    for ad, tur, ham in aday.metin_parcalari():
        if tur == "kaynak":
            continue
        t = norm(ham)
        for kalip, etiket in RECAP_KALIPLARI:
            m = re.search(kalip, t)
            if m and m.group(0) not in gorulen:
                gorulen.add(m.group(0))
                bulgular.append(Bulgu(kural="HAFTALIK_OZET", onceki=None, alan=ad, ifade=_duz(ham),
                                      aciklama=f"özet/recap dili: «{m.group(0)}» ({etiket})"))

    eslesen = []
    for h in gecmis:
        c = kor.cift(h)
        # 2. Aynı başlık
        for a in aday.baslik_cumle:
            if not a.ad.endswith(".title"):
                continue
            ka = set(kok_dizisi(a.ham))
            for b in h.baslik_cumle:
                if not b.ad.endswith(".title"):
                    continue
                kb = set(kok_dizisi(b.ham))
                if len(ka) >= 2 and len(kb) >= 2:
                    j = len(ka & kb) / len(ka | kb)
                    if j >= ESIK_BASLIK:
                        bulgular.append(Bulgu(kural="AYNI_BASLIK", onceki=h.ad, alan=f"{a.ad} ~ {b.ad}",
                                              ifade=f"«{_duz(a.ham)}» ~ «{_duz(b.ham)}»",
                                              aciklama=f"başlık kök benzerliği {j:.2f} (eşik {ESIK_BASLIK:.2f})"))
        # 3. Aynı alt konu / teknik / anlatım
        if alt_konu_tekrari_mi(c):
            eslesen.append(h)
            anah = c["nadir_ortak"] + c["nadir_bigram"]
            ek = (" (kaynak künyesi de ortak: aynı kaynak tek başına sorun değil, alt konu da örtüşüyor)"
                  if c["ortak_kaynak"] else "")
            bulgular.append(Bulgu(
                kural="ALT_KONU_TEKRARI", onceki=h.ad, alan=f"{_alan_bul(aday, anah)} ~ {_alan_bul(h, anah)}",
                ifade=", ".join(c["nadir_ortak"][:8]) + (" | ikili: " + "; ".join(" ".join(b) for b in c["nadir_bigram"][:5])
                                                         if c["nadir_bigram"] else ""),
                aciklama=f"ortak içerik oranı {c['oran']:.2f}, {len(c['nadir_ortak'])} nadir ortak kök, "
                         f"{len(c['nadir_bigram'])} ortak ikili" + ek))
        # 4. Reels önceki içeriğin soru/madde metnini taşıyor mu
        if aday.reel:
            sorular = [x for x in aday.alanlar if x.tur == "soru"]
            havuz = [x for x in h.alanlar if x.tur in ("soru", "govde") and x.cumle]
            es = []
            for q in sorular:
                kq = set(sum(q.cumle, []))
                for b in havuz:
                    kb = set(sum(b.cumle, []))
                    if len(kq) >= 2 and len(kb) >= 2 and len(kq & kb) / len(kq | kb) >= ESIK_SORU:
                        es.append((q, b))
                        break
            if len(es) >= MIN_SORU:
                bulgular.append(Bulgu(
                    kural="REELS_ONCEKI_METIN", onceki=h.ad,
                    alan="; ".join(f"{q.ad} ~ {b.ad}" for q, b in es[:5]),
                    ifade=" || ".join(f"«{_duz(q.ham, 70)}»" for q, _ in es[:3]),
                    aciklama=f"{len(es)}/{len(sorular)} Reels sorusu önceki içerikte aynen/yakın var"))
    # 5. Çok sayıda eski içeriği derleyen gönderi = özet
    if len(eslesen) >= RECAP_KAC_ESLESME:
        bulgular.append(Bulgu(kural="HAFTALIK_OZET", onceki=", ".join(h.ad for h in eslesen[:5]), alan="(tüm gönderi)",
                              ifade=f"{len(eslesen)} farklı eski içerikle alt konu örtüşmesi",
                              aciklama="birden çok önceki gönderinin içeriğini toparlıyor (özet/derleme)"))
    return bulgular


# ---------------------------------------------------------------- geçmiş toplama
def gecmisi_topla(aday, dizin):
    out = []
    for p in sorted(Path(dizin).glob("*.json")):
        ad = p.name
        if p.resolve() == aday.yol.resolve() or ad.startswith("taslak-"):
            continue
        m = re.match(r"(\d{4}-\d{2}-\d{2})", ad)
        if not m:
            continue
        if aday.tarih and m.group(1) > aday.tarih:
            continue
        # yinelenen dosya adı aynı taban (carousel+reel) ayrı sayılır; kendi tabanı geçmiş değildir
        try:
            out.append(Icerik(p, aciklama_zorunlu=False))
        except (ValueError, KeyError, json.JSONDecodeError):
            continue
    return out


def calistir(yol, dizin=None):
    aday = Icerik(yol)
    dizin = dizin or aday.yol.parent
    gecmis = gecmisi_topla(aday, dizin)
    bulgular = denetle(aday, gecmis)
    return aday, gecmis, bulgular


def rapor(aday, gecmis, bulgular):
    return {
        "denetim": "ruharya-tekrar-denetimi",
        "surum": 1,
        "icerik": str(aday.yol),
        "tur": "reels" if aday.reel else "carousel",
        "karsilastirilan_icerik_sayisi": len(gecmis),
        "sonuc": "ENGEL" if bulgular else "GECTI",
        "bulgular": [dict(b) for b in bulgular],
    }


def insan_metni(r):
    s = [f"Tekrar denetimi: {r['icerik']} ({r['tur']}) · {r['karsilastirilan_icerik_sayisi']} önceki içerikle karşılaştırıldı"]
    if not r["bulgular"]:
        s.append("SONUÇ: GEÇTİ")
        return "\n".join(s)
    s.append(f"SONUÇ: ENGEL ({len(r['bulgular'])} bulgu) - Buffer'a gönderme; yeni konu seç.")
    for i, b in enumerate(r["bulgular"], 1):
        s.append(f"  {i}. [{b['kural']}] önceki: {b['onceki'] or '-'}")
        s.append(f"     alan: {b['alan']}")
        s.append(f"     ifade: {b['ifade']}")
        s.append(f"     neden: {b['aciklama']}")
    return "\n".join(s)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("icerik")
    ap.add_argument("--gecmis-dizin")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--cikti")
    a = ap.parse_args(argv)
    try:
        aday, gecmis, bulgular = calistir(a.icerik, a.gecmis_dizin)
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as e:
        hata = {"denetim": "ruharya-tekrar-denetimi", "sonuc": "HATA", "hata": f"{type(e).__name__}: {e}"}
        print(json.dumps(hata, ensure_ascii=False) if a.json else f"Tekrar denetimi YAPILAMADI (engel): {hata['hata']}")
        return 2
    r = rapor(aday, gecmis, bulgular)
    if a.cikti:
        Path(a.cikti).write_text(json.dumps(r, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(r, ensure_ascii=False, indent=2) if a.json else insan_metni(r))
    return 1 if bulgular else 0


if __name__ == "__main__":
    sys.exit(main())
