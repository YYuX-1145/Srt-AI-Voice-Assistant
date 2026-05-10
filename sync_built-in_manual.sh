sed '2d' ./README.md > ./docs/en_US/README.md
for item in $(find ./docs -type f -name '*.md');do
    language="$(awk -F '/' '{print($(NF-1))}' <<< $item)"
    name="$(basename $item .md)"
    mkdir -p "./Sava_Utils/man/$language"
    cat <(echo -e "$name = r\"\"\"") $item <(echo -e "\n\"\"\"") > ./Sava_Utils/man/$language/$name.py
    #echo $language $name
done