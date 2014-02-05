for file in *
do
  rm $file/grammar.zgr 2>/dev/null
  ln -s ../../../grammars/$file.zgr $file/grammar.zgr 2>/dev/null
done
