IFS=$'\n'
for file in $(find -type f -name '*.py');do
    for line in $(grep -oP "i18n\('\K[^']*(?='\))" $file);do
        if ! grep -Fq "\"$line\"" './Sava_Utils/i18nAuto/translations/zh_CN.py';then
            echo $line
        fi
    done
done