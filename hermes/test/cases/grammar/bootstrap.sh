for file in parsing/*
do
  rm $file/grammar.zgr
  ln -s ../../../../grammars/$file.zgr $file/grammar.zgr
done
