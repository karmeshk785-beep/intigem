name: Build APK
on: [push, workflow_dispatch]
jobs:
  build:
    runs-on: ubuntu-22.04
    steps:
      - uses: actions/checkout@v4
      - uses: ArtemSBulgarian/buildozer-action@v1
        with:
          command: buildozer android debug
      - uses: actions/upload-artifact@v4
        with:
          name: intigem-apk
          path: bin/*.apk
