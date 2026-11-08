import threading
from kivy.app import App
from kivy.clock import Clock
from kivy.uix.label import Label
from android.runnable import run_on_ui_thread
from jnius import autoclass

import server

WebView = autoclass("android.webkit.WebView")
WebViewClient = autoclass("android.webkit.WebViewClient")
activity = autoclass("org.kivy.android.PythonActivity").mActivity

threading.Thread(
    target=lambda: server.HTTPServer(("127.0.0.1", 8080), server.H).serve_forever(),
    daemon=True,
).start()


@run_on_ui_thread
def open_webview(*args):
    w = WebView(activity)
    s = w.getSettings()
    s.setJavaScriptEnabled(True)
    s.setDomStorageEnabled(True)
    w.setWebViewClient(WebViewClient())
    activity.setContentView(w)
    w.loadUrl("http://127.0.0.1:8080")


class LocalStudio(App):
    def build(self):
        Clock.schedule_once(open_webview, 1)
        return Label(text="Loading...")


LocalStudio().run()
