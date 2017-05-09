## Pinyin Toolkit

An addon for Mandarin Chinese pinyin in the Anki Spaced Repetition System (http://ankisrs.net/)

Addon page at https://ankiweb.net/shared/info/2554990764
Documentation at http://batterseapower.github.io/pinyin-toolkit/ 
Google Discussion Group at http://is.gd/LK9v2g
List of issues at https://github.com/chatch/pinyin-toolkit/issues

### Building the plugin

```
git clone https://github.com/chanind/pinyin-toolkit.git
git submodule init
git submodule update
python pinyin/db/builder.py
./make_zip.sh                   # build package for upload to anki addons page <br>
cp -rf * ~/Anki/addons          # install direct to local addons directory
```
