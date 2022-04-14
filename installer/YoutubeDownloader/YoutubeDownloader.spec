# -*- mode: python ; coding: utf-8 -*-

block_cipher = None


a = Analysis(['..\\YoutubeDownloader.py'],
             pathex=['C:\\Users\\Chris\\PycharmProjects\\ytdlgui\\installer\\YoutubeDownloader'],
             binaries=[('C:\\Program Files\\FFMPEG\\ffmpeg-20200831-4a11a6f-win64-static\\bin\\ffmpeg.exe', 'ffmpeg.exe')],
             datas=[('C:\\Users\\Chris\\AppData\\Local\\Programs\\Python\\Python39\\Lib\\site-packages\\ttkbootstrap', 'ttkbootstrap')],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          name='YoutubeDownloader',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=False )
