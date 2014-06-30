for link in $(find . | grep '.zgr')
do
  filename=$(basename $(readlink -f $link))
  dirname=$(dirname $link)
  echo $link, $filename, $dirname
  rm $link
  ln -s ../../../grammars/parsing/$filename $dirname/grammar.zgr
done
