for file in *
do
  rm $file/first.json $file/follow.json $file/conflicts.json $file/tokens $file/ast $file/parse_tree 2>/dev/null
done
