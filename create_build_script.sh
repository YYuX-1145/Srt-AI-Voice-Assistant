#ex: $1 = pyinstaller
echo -n "$1 " > build_sava.bat
for i in $(find ./Sava_Utils/man -type f -name '*.py' );do
    module_name=$(basename $i .py)
    if [ $module_name != "__init__" ];then
        dn=$(dirname $i)
        dn=$(basename $dn)
        module_name="Sava_Utils.man.$dn.$module_name"
        echo -n "--hidden-import=$module_name " >> build_sava.bat
    fi
done
for i in $(find ./Sava_Utils/i18nAuto/translations -type f -name '*.py');do
    module_name=$(basename $i .py)
    if [ $module_name != "__init__" ];then
        module_name="Sava_Utils.i18nAuto.translations.$module_name"
        echo -n "--hidden-import=$module_name " >> build_sava.bat
    fi
done
echo '-F Srt-AI-Voice-Assistant.py' >> build_sava.bat
echo 'pause' >> build_sava.bat
