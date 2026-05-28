[app]

title = ReadAfterMe

package.name = readafterme

package.domain = org.readafterme

source.dir = .

source.include_exts = py,png,jpg,kv,atlas,ttf

version = 0.1

requirements = python3,kivy,plyer,requests,pyjnius,soundfile,sounddevice,numpy

orientation = portrait

fullscreen = 0

android.permissions = INTERNET,RECORD_AUDIO,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE,READ_MEDIA_AUDIO

android.api = 34

android.minapi = 26

android.ndk = 27

android.sdk = 34

android.gradle_dependencies =

android.archs = arm64-v8a

android.private_storage = True

android.wakelock = True
