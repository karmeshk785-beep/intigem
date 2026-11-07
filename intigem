import json, threading, urllib.request, os
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.clock import Clock

def groq(key, q):
    body = json.dumps({"model": "llama-3.3-70b-versatile",
                       "messages": [{"role": "user", "content": q}]}).encode()
    req = urllib.request.Request("https://api.groq.com/openai/v1/chat/completions",
                                 data=body,
                                 headers={"Content-Type": "application/json",
                                          "Authorization": "Bearer " + key,
                                          "User-Agent": "Mozilla/5.0"})
    res = json.loads(urllib.request.urlopen(req, timeout=40).read())
    return res["choices"][0]["message"]["content"]

class IntigemApp(App):
    def build(self):
        self.keyfile = os.path.join(self.user_data_dir, "groq_key.txt")
        self.key = open(self.keyfile).read().strip() if os.path.exists(self.keyfile) else ""
        root = BoxLayout(orientation="vertical", padding=10, spacing=8)
        self.keybox = TextInput(hint_text="Groq key (gsk_...)", password=True,
                                multiline=False, size_hint_y=None, height=50)
        save = Button(text="Key save karo", size_hint_y=None, height=50)
        save.bind(on_press=self.save_key)
        self.q = TextInput(hint_text="Sawal likho", multiline=False,
                           size_hint_y=None, height=50)
        ask = Button(text="Pucho", size_hint_y=None, height=50)
        ask.bind(on_press=self.ask)
        self.out = Label(text="Intigem taiyaar hai.", size_hint_y=None,
                         halign="left", valign="top")
        self.out.bind(width=lambda i, w: setattr(i, "text_size", (w, None)))
        self.out.bind(texture_size=lambda i, s: setattr(i, "height", s[1]))
        sv = ScrollView()
        sv.add_widget(self.out)
        for w in (self.keybox, save, self.q, ask):
            root.add_widget(w)
        root.add_widget(sv)
        return root

    def show(self, txt):
        Clock.schedule_once(lambda dt: setattr(self.out, "text", txt))

    def save_key(self, *a):
        self.key = self.keybox.text.strip()
        with open(self.keyfile, "w") as f:
            f.write(self.key)
        self.keybox.text = ""
        self.show("Key save ho gayi.")

    def ask(self, *a):
        q = self.q.text.strip()
        if not q:
            return
        if not self.key:
            self.show("Pehle key save karo.")
            return
        self.show("Soch raha hoon...")
        threading.Thread(target=self.run_ask, args=(q,), daemon=True).start()

    def run_ask(self, q):
        try:
            self.show("Intigem: " + groq(self.key, q))
        except Exception as e:
            self.show("Error: " + str(e))

IntigemApp().run()
