"""calistir.sh için dış ağ/yayın yapmayan gerçek betik entegrasyon testleri."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parent / "calistir.sh"


class CalistirTest(unittest.TestCase):
    def setUp(self):
        self.home = Path(tempfile.mkdtemp(prefix="ruharya-calistir-test-"))
        self.repo = self.home / "ruharya-content"
        self.bin = self.repo / ".venv" / "bin"
        self.veri = self.home / "zeus" / "ruharya"
        self.panel = self.home / "zeus-panel"
        self.zeus = self.home / "zeus"
        for d in (self.bin, self.veri, self.panel, self.zeus):
            d.mkdir(parents=True, exist_ok=True)
        (self.repo / "build").mkdir()
        (self.panel / ".venv" / "bin").mkdir(parents=True)
        (self.panel / ".venv" / "bin" / "python").symlink_to(Path(sys.executable))
        self.zg_log = self.home / "zg.jsonl"
        self.tg_log = self.home / "telegram.txt"
        self.argv_log = self.home / "claude-argv.json"
        self._exe(self.bin / "git", "#!/usr/bin/env bash\nexit 0\n")
        self._exe(self.zeus / "zeus-gorev", """#!/usr/bin/env python3
import json, os, sys
with open(os.environ['FAKE_ZG_LOG'], 'a', encoding='utf-8') as f:
    f.write(json.dumps(sys.argv[1:]) + '\\n')
if sys.argv[1] == 'dis-basla':
    print('test-gorev')
""")
        self._exe(self.bin / "claude", """#!/usr/bin/env python3
import json, os, sys
with open(os.environ['FAKE_ARGV'], 'w', encoding='utf-8') as f:
    json.dump(sys.argv[1:], f)
mode = os.environ.get('FAKE_CLAUDE_MODE', 'success')
if mode == 'max_turns':
    d = {'type': 'result', 'subtype': 'error_max_turns', 'is_error': True,
         'result': None, 'errors': ['Reached maximum number of turns (15)']}
else:
    d = {'type': 'result', 'subtype': 'success', 'is_error': False,
         'result': 'Apollon: Kuru test gönderisi hazır.'}
print(json.dumps(d))
sys.exit(int(os.environ.get('FAKE_CLAUDE_EXIT', '0')))
""")
        (self.panel / "telegram_bildir.py").write_text("""import os, sys
metin = sys.stdin.read()
with open(os.environ['FAKE_TELEGRAM_LOG'], 'a', encoding='utf-8') as f:
    f.write(metin + '\\n')
sys.exit(int(os.environ.get('FAKE_TELEGRAM_EXIT', '0')))
""", encoding="utf-8")

    @staticmethod
    def _exe(path, text):
        path.write_text(text, encoding="utf-8")
        path.chmod(0o755)

    def calistir(self, **degisiklik):
        env = dict(os.environ, HOME=str(self.home), FAKE_ZG_LOG=str(self.zg_log),
                   FAKE_TELEGRAM_LOG=str(self.tg_log), FAKE_ARGV=str(self.argv_log))
        env.update({k: str(v) for k, v in degisiklik.items()})
        return subprocess.run(["bash", str(SCRIPT), "gunluk"], cwd=self.repo, env=env,
                              capture_output=True, text=True, timeout=15)

    def zg_cagrilari(self):
        return [json.loads(x) for x in self.zg_log.read_text(encoding="utf-8").splitlines()]

    def test_json_max_turns_cli_sifir_donse_bile_hata(self):
        r = self.calistir(FAKE_CLAUDE_MODE="max_turns", FAKE_CLAUDE_EXIT=0)
        self.assertEqual(r.returncode, 1, r.stderr)
        bitis = [x for x in self.zg_cagrilari() if x[0] == "bitir"]
        self.assertEqual(len(bitis), 1)
        self.assertIn("--hata", bitis[0])
        ozet = bitis[0][bitis[0].index("--ozet") + 1]
        self.assertIn("Reached maximum number of turns (15)", ozet)

    def test_telegram_hatasi_basariyi_ve_sonraki_kilidi_bozmaz(self):
        r1 = self.calistir(FAKE_TELEGRAM_EXIT=1)
        r2 = self.calistir(FAKE_TELEGRAM_EXIT=1)
        self.assertEqual((r1.returncode, r2.returncode), (0, 0), (r1.stderr, r2.stderr))
        C = self.zg_cagrilari()
        self.assertEqual(len([x for x in C if x[0] == "dis-basla"]), 2)
        bitis = [x for x in C if x[0] == "bitir"]
        self.assertEqual(len(bitis), 2)
        self.assertTrue(all("--hata" not in x for x in bitis))


if __name__ == "__main__":
    unittest.main()
