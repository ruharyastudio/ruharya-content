#!/usr/bin/env bash
# Ruharya çalıştırıcısı (Zeus sunucusu). Kullanım: calistir.sh gunluk|haftalik
#   RUHARYA_TASLAK=1 → günlük gönderiyi yalnızca Buffer TASLAĞI olarak üret (bkz. zeus/ruharya-instagram.md)
# Claude Code'u headless (claude -p) çalıştırır, çıktıyı ~/zeus/ruharya/loglar/'a yazar,
# sonunda Ali'ye Telegram'dan tek paragraf özet gönderir. Gizli bilgi içermez (repo herkese açık).
set -uo pipefail
TUR="${1:?gunluk|haftalik}"
REPO="$HOME/ruharya-content"
VERI="$HOME/zeus/ruharya"
LOGD="$VERI/loglar"
PY="$HOME/zeus-panel/.venv/bin/python"
export PATH="$REPO/.venv/bin:$HOME/.hermes/tools/node-26.12.1-linux-x64/bin:$HOME/.local/bin:/usr/local/bin:/usr/bin:/bin"
export TZ=Europe/Istanbul
mkdir -p "$LOGD" "$REPO/build"
DAMGA="$(date +%Y%m%d-%H%M)"
[[ "${RUHARYA_TASLAK:-0}" == "1" ]] && EK="-taslak" || EK=""
LOG="$LOGD/$DAMGA-$TUR$EK"

bildir() { printf '%s' "$1" | "$PY" "$HOME/zeus-panel/telegram_bildir.py" || true; }

# aynı anda tek Claude Code işi
exec 9>"$VERI/.calistir.kilit"
if ! flock -n 9; then bildir "⚠️ Ruharya $TUR: başka bir Ruharya işi sürüyor, bu çalışma atlandı."; exit 0; fi

# Atlanacak günler: ~/zeus/ruharya/ayarlar.json → "atla_tarihleri": ["YYYY-MM-DD", ...] (yalnızca günlük, normal mod)
if [[ "$TUR" == "gunluk" && -z "$EK" ]]; then
  BUGUN="$(date +%F)"
  if "$PY" -c 'import json,sys; a=json.load(open(sys.argv[1])); sys.exit(0 if sys.argv[2] in (a.get("atla_tarihleri") or []) else 1)' \
       "$VERI/ayarlar.json" "$BUGUN" 2>/dev/null; then
    echo "$BUGUN atla_tarihleri içinde; üretim yapılmadı" >"$LOG.atlandi"
    bildir "⏭️ Ruharya günlük: $BUGUN üretimi atlandı (ayarlar: atla_tarihleri). Bugünün gönderisi zaten zamanlı."
    exit 0
  fi
fi

# Görev Merkezi kaydı (panelde canlı görünür; servis kapalıysa iş yine çalışır)
ZG="$HOME/zeus/zeus-gorev"; GCIKTI=""; GOZET=""
case "$TUR" in gunluk) GAJAN=icerik-uretici; GBAS="Ruharya günlük gönderi$([[ -n $EK ]] && echo " (taslak)")";; *) GAJAN=pazar-analizi; GBAS="Ruharya haftalık rapor";; esac
GID="$("$ZG" dis-basla --kaynak ruharya --ajan "$GAJAN" --baslik "$GBAS" --pid $$ 2>/dev/null || true)"
gasama() { if [[ -n "$GID" ]]; then "$ZG" asama "$GID" "$1" >/dev/null 2>&1 || true; fi; }
gbitir() {
  local kod=$? a=()
  [[ -z "$GID" ]] && return $kod
  if [[ $kod -ne 0 ]]; then a+=(--hata "çıkış kodu $kod"); elif [[ "$GOZET" == HATA* ]]; then a+=(--hata "${GOZET:0:300}"); fi
  [[ -n "$GCIKTI" && -f "$GCIKTI" ]] && a+=(--cikti "$GCIKTI")
  [[ -n "$GOZET" ]] && a+=(--ozet "$GOZET")
  "$ZG" bitir "$GID" "${a[@]}" >/dev/null 2>&1 || true
  return $kod
}
trap gbitir EXIT
gasama "depo güncelleniyor (git pull)"

cd "$REPO" || exit 1
if ! git pull -q --rebase origin main >"$LOG.git.log" 2>&1; then
  bildir "⚠️ Ruharya $TUR başlamadı: depo güncellenemedi (git pull). Ayrıntı: $LOG.git.log"; exit 1
fi

case "$TUR" in
  gunluk)
    BECERI="zeus/ruharya-instagram.md"; ORIJ=".claude/skills/ruharya-instagram/SKILL.md"; BASLIK="📸 Ruharya günlük"
    if [[ -n "$EK" ]]; then
      MOD="TASLAK MODU (RUHARYA_TASLAK=1): zeus/ruharya-instagram.md'deki taslak kurallarına uy. Gönderiyi üret, 'taslak-' önekli klasöre koy, push et ve Buffer'a YALNIZCA taslak olarak ekle; zamanlama yapma; repodaki content/yayin-kaydi.md, konu havuzu ve fikir durumlarını değiştirme (Zeus verisine yalnızca taslak- önekli draft kaydı yaz)."
      BASLIK="🧪 Ruharya TASLAK deneme"
    else
      MOD="NORMAL MOD: bugünün gönderisini üret ve zamanla."
    fi ;;
  haftalik)
    BECERI="zeus/ruharya-strateji.md"; ORIJ=".claude/skills/ruharya-strateji/SKILL.md"; BASLIK="📊 Ruharya haftalık rapor"
    MOD="Haftalık strateji raporunu hazırla." ;;
  *) echo "bilinmeyen tür: $TUR"; exit 2 ;;
esac

GOREV="Bugün $(date '+%Y-%m-%d %A %H:%M') (Europe/Istanbul). $MOD
Önce $BECERI dosyasını, sonra orada istenen $ORIJ dosyasını oku ve adımları eksiksiz uygula.
Kurallar: sudo kullanma; ~/.hermes/.env dosyasını okuma veya gösterme; dosya silme. Uydurma bilgi yok.
Bitince son mesajın, $BECERI dosyasındaki 'Son mesaj' bölümüne uygun TEK paragraf olsun (Ali'ye Telegram'dan aynen gider)."

gasama "Claude Code çalışıyor: $([[ $TUR == gunluk ]] && echo içerik üretimi || echo strateji raporu)"
GCIKTI="$LOG.json"
claude -p "$GOREV" \
  --output-format json \
  --permission-mode acceptEdits \
  --allowed-tools "Read Edit Write Glob Grep WebSearch WebFetch Bash(git *) Bash(curl *) Bash(npm *) Bash(ls *) Bash(date *) Bash(sleep *) Bash(.venv/bin/python *) Bash(python3 *) Bash($PY *)" \
  --add-dir "$VERI" \
  >"$LOG.json" 2>"$LOG.err"
KOD=$?

OZET="$("$PY" - "$LOG.json" <<'PY'
import json, sys
try:
    d = json.load(open(sys.argv[1], encoding="utf-8"))
    r = (d.get("result") or "").strip()
    print(("HATA: " if d.get("is_error") else "") + (r or "(boş yanıt)"))
except Exception as e:
    print(f"HATA: Claude çıktısı okunamadı ({type(e).__name__})")
PY
)"
gasama "özet Telegram'a gönderiliyor"
GOZET="$OZET"
if [[ $KOD -ne 0 && "$OZET" != HATA:* ]]; then OZET="HATA (çıkış $KOD): $OZET $(tail -c 300 "$LOG.err")"; fi
bildir "$BASLIK
$OZET
(log: $(basename "$LOG").json)"
exit $KOD
